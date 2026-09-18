use std::{
    collections::HashSet,
    fs::{self, OpenOptions},
    io::{self, Write},
    net::{IpAddr, Ipv4Addr, SocketAddr},
    path::{Path, PathBuf},
    sync::{
        atomic::{AtomicU64, Ordering},
        Arc, Mutex,
    },
    time::{Duration, Instant},
};

use base64::{engine::general_purpose::URL_SAFE_NO_PAD, Engine as _};
use futures_util::{SinkExt, StreamExt};
use serde::{Deserialize, Serialize};
use subtle::ConstantTimeEq;
use tauri::{AppHandle, Emitter};
use tokio::{net::TcpListener, sync::mpsc, time};
use tokio_tungstenite::{
    accept_hdr_async,
    tungstenite::{
        handshake::server::{ErrorResponse, Request, Response},
        http,
        protocol::{frame::coding::CloseCode, CloseFrame},
        Message,
    },
};
use url::Url;

pub const BRIDGE_ADDRESS: SocketAddr = SocketAddr::new(IpAddr::V4(Ipv4Addr::LOCALHOST), 17_321);
const BRIDGE_PATH: &str = "/extension/v1";
const EXTENSION_ORIGIN: &str = "chrome-extension://ialnhniheceignniocihlaoojdbapnjj";
const SECRET_FILE: &str = "extension-bridge-secret";
const PROTOCOL_VERSION: u8 = 1;
const HELLO_TIMEOUT: Duration = Duration::from_secs(5);
const HEARTBEAT_TIMEOUT: Duration = Duration::from_secs(65);
const MAX_MESSAGE_BYTES: usize = 16 * 1024;

#[derive(Clone)]
pub struct BridgeState {
    inner: Arc<BridgeInner>,
}

struct BridgeInner {
    secret_path: PathBuf,
    secret: Mutex<String>,
    runtime: Mutex<RuntimeState>,
    next_connection_id: AtomicU64,
}

struct RuntimeState {
    mode: AutoOpenMode,
    listener_status: ListenerStatus,
    connection: Option<ConnectionHandle>,
    target_selected: bool,
    pending_navigation_ids: HashSet<String>,
}

struct ConnectionHandle {
    id: u64,
    sender: mpsc::UnboundedSender<Message>,
}

#[derive(Clone, Copy, Debug, Default, Deserialize, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum AutoOpenMode {
    #[default]
    Off,
    NewTab,
    CurrentAxiomTab,
}

#[derive(Clone, Copy, Debug, PartialEq)]
enum ListenerStatus {
    Starting,
    Ready,
    PortInUse,
    Unavailable,
}

#[derive(Clone, Debug, PartialEq, Serialize)]
#[serde(rename_all = "camelCase")]
pub struct BridgeSnapshot {
    listener_status: &'static str,
    connection_status: &'static str,
    target_status: &'static str,
    mode: AutoOpenMode,
}

#[derive(Clone, Debug, Deserialize)]
#[serde(tag = "type", rename_all = "snake_case", deny_unknown_fields)]
enum ExtensionMessage {
    Hello {
        #[serde(rename = "protocolVersion")]
        protocol_version: u8,
        #[serde(rename = "extensionVersion")]
        extension_version: String,
        #[serde(rename = "pairingSecret")]
        pairing_secret: String,
    },
    SetMode {
        #[serde(rename = "protocolVersion")]
        protocol_version: u8,
        #[serde(rename = "requestId")]
        request_id: String,
        mode: ExtensionMode,
    },
    NavigationResult {
        #[serde(rename = "protocolVersion")]
        protocol_version: u8,
        #[serde(rename = "commandId")]
        command_id: String,
        status: NavigationStatus,
        method: Option<NavigationMethod>,
        #[serde(rename = "errorCode")]
        error_code: Option<String>,
    },
    Ping {
        #[serde(rename = "protocolVersion")]
        protocol_version: u8,
        #[serde(rename = "sentAt")]
        sent_at: String,
    },
}

#[derive(Clone, Copy, Debug, Deserialize, Serialize)]
#[serde(rename_all = "snake_case")]
enum ExtensionMode {
    Off,
    CurrentAxiomTab,
}

impl From<ExtensionMode> for AutoOpenMode {
    fn from(mode: ExtensionMode) -> Self {
        match mode {
            ExtensionMode::Off => Self::Off,
            ExtensionMode::CurrentAxiomTab => Self::CurrentAxiomTab,
        }
    }
}

#[derive(Clone, Copy, Debug, Deserialize, Serialize)]
#[serde(rename_all = "snake_case")]
enum NavigationStatus {
    Completed,
    Superseded,
    Ignored,
    Failed,
}

#[derive(Clone, Copy, Debug, Deserialize, Serialize)]
#[serde(rename_all = "snake_case")]
enum NavigationMethod {
    History,
    SameTabReload,
}

#[derive(Serialize)]
#[serde(tag = "type", rename_all = "snake_case")]
enum DesktopMessage<'a> {
    State {
        #[serde(rename = "protocolVersion")]
        protocol_version: u8,
        mode: AutoOpenMode,
        #[serde(rename = "bridgeStatus")]
        bridge_status: &'static str,
    },
    Navigate {
        #[serde(rename = "protocolVersion")]
        protocol_version: u8,
        #[serde(rename = "commandId")]
        command_id: &'a str,
        url: &'a str,
        #[serde(rename = "issuedAt")]
        issued_at: &'a str,
    },
    ModeResult {
        #[serde(rename = "protocolVersion")]
        protocol_version: u8,
        #[serde(rename = "requestId")]
        request_id: &'a str,
        accepted: bool,
        mode: AutoOpenMode,
        #[serde(rename = "errorCode", skip_serializing_if = "Option::is_none")]
        error_code: Option<&'a str>,
    },
    Pong {
        #[serde(rename = "protocolVersion")]
        protocol_version: u8,
        #[serde(rename = "sentAt")]
        sent_at: &'a str,
    },
}

#[derive(Clone, Serialize)]
#[serde(rename_all = "camelCase")]
struct NavigationResultEvent {
    command_id: String,
    status: NavigationStatus,
    method: Option<NavigationMethod>,
    error_code: Option<String>,
}

#[derive(Clone, Serialize)]
struct ModeChangedEvent {
    mode: AutoOpenMode,
}

#[derive(Debug, Serialize)]
pub struct BridgeCommandError {
    code: &'static str,
}

impl BridgeCommandError {
    fn new(code: &'static str) -> Self {
        Self { code }
    }
}

impl BridgeState {
    pub fn initialize(app_data_dir: PathBuf) -> Result<Self, io::Error> {
        fs::create_dir_all(&app_data_dir)?;
        let secret_path = app_data_dir.join(SECRET_FILE);
        let secret = load_or_create_secret(&secret_path)?;
        Ok(Self {
            inner: Arc::new(BridgeInner {
                secret_path,
                secret: Mutex::new(secret),
                runtime: Mutex::new(RuntimeState {
                    mode: AutoOpenMode::Off,
                    listener_status: ListenerStatus::Starting,
                    connection: None,
                    target_selected: false,
                    pending_navigation_ids: HashSet::new(),
                }),
                next_connection_id: AtomicU64::new(1),
            }),
        })
    }

    pub fn start(&self, app: AppHandle) {
        let state = self.clone();
        tauri::async_runtime::spawn(async move {
            state.run_listener(app).await;
        });
    }

    fn snapshot(&self) -> BridgeSnapshot {
        let runtime = self.inner.runtime.lock().unwrap_or_else(|e| e.into_inner());
        BridgeSnapshot {
            listener_status: match runtime.listener_status {
                ListenerStatus::Starting => "starting",
                ListenerStatus::Ready => "ready",
                ListenerStatus::PortInUse => "port_in_use",
                ListenerStatus::Unavailable => "unavailable",
            },
            connection_status: if runtime.connection.is_some() {
                "connected"
            } else {
                "disconnected"
            },
            target_status: if runtime.target_selected {
                "selected"
            } else {
                "missing"
            },
            mode: runtime.mode,
        }
    }

    fn emit_snapshot(&self, app: &AppHandle) {
        let _ = app.emit("ascend://bridge-state", self.snapshot());
    }

    async fn run_listener(&self, app: AppHandle) {
        let listener = match TcpListener::bind(BRIDGE_ADDRESS).await {
            Ok(listener) => listener,
            Err(error) => {
                let mut runtime = self.inner.runtime.lock().unwrap_or_else(|e| e.into_inner());
                runtime.listener_status = if error.kind() == io::ErrorKind::AddrInUse {
                    ListenerStatus::PortInUse
                } else {
                    ListenerStatus::Unavailable
                };
                drop(runtime);
                self.emit_snapshot(&app);
                return;
            }
        };

        {
            let mut runtime = self.inner.runtime.lock().unwrap_or_else(|e| e.into_inner());
            runtime.listener_status = ListenerStatus::Ready;
        }
        self.emit_snapshot(&app);

        loop {
            let Ok((stream, peer)) = listener.accept().await else {
                continue;
            };
            if !peer.ip().is_loopback() {
                continue;
            }
            let connection_state = self.clone();
            let connection_app = app.clone();
            tauri::async_runtime::spawn(async move {
                connection_state
                    .handle_connection(stream, connection_app)
                    .await;
            });
        }
    }

    async fn handle_connection(&self, stream: tokio::net::TcpStream, app: AppHandle) {
        let socket = accept_hdr_async(stream, validate_handshake).await;
        let Ok(mut socket) = socket else {
            return;
        };

        let hello_message = match time::timeout(HELLO_TIMEOUT, socket.next()).await {
            Ok(Some(Ok(message))) => message,
            _ => {
                close_socket(&mut socket, 4000, "hello_required").await;
                return;
            }
        };
        let Some(ExtensionMessage::Hello {
            protocol_version,
            extension_version,
            pairing_secret,
        }) = parse_text_message(hello_message)
        else {
            close_socket(&mut socket, 4000, "invalid_hello").await;
            return;
        };

        if protocol_version != PROTOCOL_VERSION {
            close_socket(&mut socket, 4002, "protocol_mismatch").await;
            return;
        }
        if !is_compatible_extension_version(&extension_version) {
            close_socket(&mut socket, 4003, "extension_version_mismatch").await;
            return;
        }
        if !self.matches_secret(&pairing_secret) {
            close_socket(&mut socket, 4001, "pairing_rejected").await;
            return;
        }

        let connection_id = self
            .inner
            .next_connection_id
            .fetch_add(1, Ordering::Relaxed);
        let (sender, mut receiver) = mpsc::unbounded_channel();
        let previous = {
            let mut runtime = self.inner.runtime.lock().unwrap_or_else(|e| e.into_inner());
            runtime.target_selected = false;
            runtime.pending_navigation_ids.clear();
            runtime.connection.replace(ConnectionHandle {
                id: connection_id,
                sender,
            })
        };
        if let Some(previous) = previous {
            let _ = previous.sender.send(close_message(4004, "replaced"));
        }
        self.emit_snapshot(&app);
        if send_json(&mut socket, &self.state_message()).await.is_err() {
            self.clear_connection(connection_id, &app);
            return;
        }

        let mut last_message = Instant::now();
        let mut heartbeat_check = time::interval(Duration::from_secs(5));
        heartbeat_check.set_missed_tick_behavior(time::MissedTickBehavior::Delay);

        loop {
            tokio::select! {
                incoming = socket.next() => {
                    let Some(Ok(message)) = incoming else { break };
                    last_message = Instant::now();
                    if message.is_close() { break; }
                    let Some(message) = parse_text_message(message) else {
                        close_socket(&mut socket, 4000, "invalid_message").await;
                        break;
                    };
                    if !self.handle_extension_message(message, &app, &mut socket).await {
                        break;
                    }
                }
                outgoing = receiver.recv() => {
                    let Some(message) = outgoing else { break };
                    if socket.send(message).await.is_err() { break; }
                }
                _ = heartbeat_check.tick() => {
                    if last_message.elapsed() > HEARTBEAT_TIMEOUT {
                        close_socket(&mut socket, 4005, "heartbeat_timeout").await;
                        break;
                    }
                }
            }
        }
        self.clear_connection(connection_id, &app);
    }

    async fn handle_extension_message<S>(
        &self,
        message: ExtensionMessage,
        app: &AppHandle,
        socket: &mut tokio_tungstenite::WebSocketStream<S>,
    ) -> bool
    where
        S: tokio::io::AsyncRead + tokio::io::AsyncWrite + Unpin,
    {
        match message {
            ExtensionMessage::Hello { .. } => false,
            ExtensionMessage::SetMode {
                protocol_version,
                request_id,
                mode,
            } => {
                if protocol_version != PROTOCOL_VERSION || !is_uuid(&request_id) {
                    return false;
                }
                let mode = AutoOpenMode::from(mode);
                {
                    let mut runtime = self.inner.runtime.lock().unwrap_or_else(|e| e.into_inner());
                    runtime.mode = mode;
                    runtime.target_selected = mode == AutoOpenMode::CurrentAxiomTab;
                }
                let response = DesktopMessage::ModeResult {
                    protocol_version: PROTOCOL_VERSION,
                    request_id: &request_id,
                    accepted: true,
                    mode,
                    error_code: None,
                };
                let _ = app.emit("ascend://extension-mode-changed", ModeChangedEvent { mode });
                self.emit_snapshot(app);
                send_json(socket, &response).await.is_ok()
            }
            ExtensionMessage::NavigationResult {
                protocol_version,
                command_id,
                status,
                method,
                error_code,
            } => {
                if protocol_version != PROTOCOL_VERSION || !is_uuid(&command_id) {
                    return false;
                }
                let target_missing = error_code.as_deref() == Some("target_missing");
                let accepted = {
                    let mut runtime = self.inner.runtime.lock().unwrap_or_else(|e| e.into_inner());
                    if !runtime.pending_navigation_ids.remove(&command_id) {
                        false
                    } else {
                        if runtime.mode == AutoOpenMode::CurrentAxiomTab {
                            if matches!(status, NavigationStatus::Completed) {
                                runtime.target_selected = true;
                            } else if target_missing {
                                runtime.target_selected = false;
                            }
                        }
                        true
                    }
                };
                if !accepted {
                    return true;
                }
                let _ = app.emit(
                    "ascend://navigation-result",
                    NavigationResultEvent {
                        command_id,
                        status,
                        method,
                        error_code,
                    },
                );
                self.emit_snapshot(app);
                true
            }
            ExtensionMessage::Ping {
                protocol_version,
                sent_at,
            } => {
                if protocol_version != PROTOCOL_VERSION || !is_iso_timestamp(&sent_at) {
                    return false;
                }
                send_json(
                    socket,
                    &DesktopMessage::Pong {
                        protocol_version: PROTOCOL_VERSION,
                        sent_at: &sent_at,
                    },
                )
                .await
                .is_ok()
            }
        }
    }

    fn state_message(&self) -> DesktopMessage<'static> {
        let mode = self
            .inner
            .runtime
            .lock()
            .unwrap_or_else(|e| e.into_inner())
            .mode;
        DesktopMessage::State {
            protocol_version: PROTOCOL_VERSION,
            mode,
            bridge_status: "ready",
        }
    }

    fn matches_secret(&self, candidate: &str) -> bool {
        let secret = self.inner.secret.lock().unwrap_or_else(|e| e.into_inner());
        bool::from(secret.as_bytes().ct_eq(candidate.as_bytes()))
    }

    fn clear_connection(&self, id: u64, app: &AppHandle) {
        let cleared = {
            let mut runtime = self.inner.runtime.lock().unwrap_or_else(|e| e.into_inner());
            if runtime
                .connection
                .as_ref()
                .is_some_and(|connection| connection.id == id)
            {
                runtime.connection = None;
                runtime.pending_navigation_ids.clear();
                true
            } else {
                false
            }
        };
        if cleared {
            self.emit_snapshot(app);
        }
    }

    fn set_mode(&self, mode: AutoOpenMode, app: &AppHandle) {
        let message = {
            let mut runtime = self.inner.runtime.lock().unwrap_or_else(|e| e.into_inner());
            runtime.mode = mode;
            if mode != AutoOpenMode::CurrentAxiomTab {
                runtime.target_selected = false;
            }
            runtime.connection.as_ref().map(|connection| {
                (
                    connection.sender.clone(),
                    json_message(&DesktopMessage::State {
                        protocol_version: PROTOCOL_VERSION,
                        mode,
                        bridge_status: "ready",
                    }),
                )
            })
        };
        if let Some((sender, Some(message))) = message {
            let _ = sender.send(message);
        }
        self.emit_snapshot(app);
    }

    fn send_navigation(
        &self,
        command_id: &str,
        url: &str,
        issued_at: &str,
    ) -> Result<(), BridgeCommandError> {
        if !is_uuid(command_id) || !is_iso_timestamp(issued_at) {
            return Err(BridgeCommandError::new("invalid_command"));
        }
        validate_axiom_url(url).map_err(|_| BridgeCommandError::new("invalid_axiom_url"))?;
        let sender = {
            let mut runtime = self.inner.runtime.lock().unwrap_or_else(|e| e.into_inner());
            if runtime.mode != AutoOpenMode::CurrentAxiomTab {
                return Err(BridgeCommandError::new("mode_inactive"));
            }
            let sender = runtime
                .connection
                .as_ref()
                .map(|connection| connection.sender.clone())
                .ok_or_else(|| BridgeCommandError::new("extension_unavailable"))?;
            if !runtime.pending_navigation_ids.insert(command_id.to_owned()) {
                return Err(BridgeCommandError::new("duplicate_command"));
            }
            sender
        };
        let message = json_message(&DesktopMessage::Navigate {
            protocol_version: PROTOCOL_VERSION,
            command_id,
            url,
            issued_at,
        })
        .ok_or_else(|| BridgeCommandError::new("serialization_failed"))?;
        if sender.send(message).is_err() {
            self.inner
                .runtime
                .lock()
                .unwrap_or_else(|e| e.into_inner())
                .pending_navigation_ids
                .remove(command_id);
            return Err(BridgeCommandError::new("extension_unavailable"));
        }
        Ok(())
    }

    fn rotate_secret(&self, app: &AppHandle) -> Result<String, BridgeCommandError> {
        let secret =
            generate_secret().map_err(|_| BridgeCommandError::new("secret_generation_failed"))?;
        write_secret(&self.inner.secret_path, &secret)
            .map_err(|_| BridgeCommandError::new("secret_storage_failed"))?;
        *self.inner.secret.lock().unwrap_or_else(|e| e.into_inner()) = secret.clone();
        let connection = self
            .inner
            .runtime
            .lock()
            .unwrap_or_else(|e| e.into_inner())
            .connection
            .take();
        self.inner
            .runtime
            .lock()
            .unwrap_or_else(|e| e.into_inner())
            .pending_navigation_ids
            .clear();
        if let Some(connection) = connection {
            let _ = connection
                .sender
                .send(close_message(4001, "pairing_rotated"));
        }
        self.emit_snapshot(app);
        Ok(secret)
    }
}

#[tauri::command]
pub fn get_extension_bridge_state(state: tauri::State<'_, BridgeState>) -> BridgeSnapshot {
    state.snapshot()
}

#[tauri::command]
pub fn get_extension_pairing_code(state: tauri::State<'_, BridgeState>) -> String {
    state
        .inner
        .secret
        .lock()
        .unwrap_or_else(|e| e.into_inner())
        .clone()
}

#[tauri::command]
pub fn rotate_extension_pairing_code(
    state: tauri::State<'_, BridgeState>,
    app: AppHandle,
) -> Result<String, BridgeCommandError> {
    state.rotate_secret(&app)
}

#[tauri::command]
pub fn set_extension_auto_open_mode(
    mode: AutoOpenMode,
    state: tauri::State<'_, BridgeState>,
    app: AppHandle,
) {
    state.set_mode(mode, &app);
}

#[tauri::command]
pub fn send_extension_navigation(
    command_id: String,
    url: String,
    issued_at: String,
    state: tauri::State<'_, BridgeState>,
) -> Result<(), BridgeCommandError> {
    state.send_navigation(&command_id, &url, &issued_at)
}

#[allow(clippy::result_large_err)]
fn validate_handshake(request: &Request, response: Response) -> Result<Response, ErrorResponse> {
    let path_ok = request.uri().path() == BRIDGE_PATH && request.uri().query().is_none();
    let origin_ok = request
        .headers()
        .get("origin")
        .and_then(|value| value.to_str().ok())
        .is_some_and(|origin| origin == EXTENSION_ORIGIN);
    if path_ok && origin_ok {
        Ok(response)
    } else {
        Err(http_error_response())
    }
}

fn http_error_response() -> ErrorResponse {
    http::Response::builder()
        .status(http::StatusCode::FORBIDDEN)
        .body(Some("Forbidden".to_owned()))
        .expect("static error response")
}

fn parse_text_message(message: Message) -> Option<ExtensionMessage> {
    let Message::Text(text) = message else {
        return None;
    };
    if text.len() > MAX_MESSAGE_BYTES {
        return None;
    }
    serde_json::from_str(&text).ok()
}

fn json_message(value: &impl Serialize) -> Option<Message> {
    serde_json::to_string(value).ok().map(Message::text)
}

async fn send_json<S>(
    socket: &mut tokio_tungstenite::WebSocketStream<S>,
    value: &impl Serialize,
) -> Result<(), ()>
where
    S: tokio::io::AsyncRead + tokio::io::AsyncWrite + Unpin,
{
    let message = json_message(value).ok_or(())?;
    socket.send(message).await.map_err(|_| ())
}

fn close_message(code: u16, reason: &'static str) -> Message {
    Message::Close(Some(CloseFrame {
        code: CloseCode::Library(code),
        reason: reason.into(),
    }))
}

async fn close_socket<S>(
    socket: &mut tokio_tungstenite::WebSocketStream<S>,
    code: u16,
    reason: &'static str,
) where
    S: tokio::io::AsyncRead + tokio::io::AsyncWrite + Unpin,
{
    let _ = socket.send(close_message(code, reason)).await;
    let _ = socket.close(None).await;
}

fn is_compatible_extension_version(version: &str) -> bool {
    let parts = version.split('.').collect::<Vec<_>>();
    parts.len() == 3
        && parts[0] == env!("CARGO_PKG_VERSION_MAJOR")
        && parts.iter().all(|part| {
            !part.is_empty() && part.chars().all(|character| character.is_ascii_digit())
        })
}

fn is_uuid(value: &str) -> bool {
    let bytes = value.as_bytes();
    bytes.len() == 36
        && bytes.iter().enumerate().all(|(index, byte)| {
            if matches!(index, 8 | 13 | 18 | 23) {
                *byte == b'-'
            } else if index == 14 {
                matches!(*byte, b'1'..=b'8')
            } else if index == 19 {
                matches!(*byte, b'8' | b'9' | b'a' | b'b' | b'A' | b'B')
            } else {
                byte.is_ascii_hexdigit()
            }
        })
}

fn is_iso_timestamp(value: &str) -> bool {
    let bytes = value.as_bytes();
    if bytes.len() != 24
        || bytes[4] != b'-'
        || bytes[7] != b'-'
        || bytes[10] != b'T'
        || bytes[13] != b':'
        || bytes[16] != b':'
        || bytes[19] != b'.'
        || bytes[23] != b'Z'
        || bytes.iter().enumerate().any(|(index, byte)| {
            !matches!(index, 4 | 7 | 10 | 13 | 16 | 19 | 23) && !byte.is_ascii_digit()
        })
    {
        return false;
    }

    let number = |start: usize, end: usize| value[start..end].parse::<u32>().ok();
    let (Some(year), Some(month), Some(day), Some(hour), Some(minute), Some(second)) = (
        number(0, 4),
        number(5, 7),
        number(8, 10),
        number(11, 13),
        number(14, 16),
        number(17, 19),
    ) else {
        return false;
    };
    let leap_year =
        year.is_multiple_of(4) && (!year.is_multiple_of(100) || year.is_multiple_of(400));
    let max_day = match month {
        1 | 3 | 5 | 7 | 8 | 10 | 12 => 31,
        4 | 6 | 9 | 11 => 30,
        2 if leap_year => 29,
        2 => 28,
        _ => return false,
    };
    (1..=max_day).contains(&day) && hour < 24 && minute < 60 && second < 60
}

fn validate_axiom_url(value: &str) -> Result<(), ()> {
    let url = Url::parse(value).map_err(|_| ())?;
    if url.scheme() != "https"
        || url.host_str() != Some("axiom.trade")
        || url.port().is_some()
        || !url.username().is_empty()
        || url.password().is_some()
        || url.fragment().is_some()
    {
        return Err(());
    }
    let mut segments = url.path_segments().ok_or(())?;
    if segments.next() != Some("meme") {
        return Err(());
    }
    let address = segments.next().ok_or(())?;
    if address.is_empty()
        || segments.next().is_some()
        || !address
            .chars()
            .all(|character| character.is_ascii_alphanumeric() || matches!(character, '-' | '_'))
    {
        return Err(());
    }
    let mut has_chain = false;
    for (key, value) in url.query_pairs() {
        if !matches!(
            key.as_ref(),
            "chain" | "chains" | "pulseChains" | "trackerChains" | "discoverChains"
        ) || !value.split(',').all(|chain| matches!(chain, "sol" | "bsc"))
        {
            return Err(());
        }
        if key == "chain" {
            if has_chain {
                return Err(());
            }
            has_chain = true;
        }
    }
    has_chain.then_some(()).ok_or(())
}

fn load_or_create_secret(path: &Path) -> Result<String, io::Error> {
    match fs::read_to_string(path) {
        Ok(secret) if is_valid_secret(secret.trim()) => Ok(secret.trim().to_owned()),
        Ok(_) => {
            let secret = generate_secret()?;
            write_secret(path, &secret)?;
            Ok(secret)
        }
        Err(error) if error.kind() == io::ErrorKind::NotFound => {
            let secret = generate_secret()?;
            write_secret(path, &secret)?;
            Ok(secret)
        }
        Err(error) => Err(error),
    }
}

fn generate_secret() -> Result<String, io::Error> {
    let mut bytes = [0_u8; 32];
    getrandom::fill(&mut bytes)
        .map_err(|_| io::Error::other("operating system random source unavailable"))?;
    Ok(URL_SAFE_NO_PAD.encode(bytes))
}

fn is_valid_secret(secret: &str) -> bool {
    URL_SAFE_NO_PAD
        .decode(secret)
        .is_ok_and(|decoded| decoded.len() == 32)
}

fn write_secret(path: &Path, secret: &str) -> Result<(), io::Error> {
    let mut options = OpenOptions::new();
    options.create(true).truncate(true).write(true);
    #[cfg(unix)]
    {
        use std::os::unix::fs::OpenOptionsExt;
        options.mode(0o600);
    }
    let mut file = options.open(path)?;
    file.write_all(secret.as_bytes())?;
    file.sync_all()
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn generated_secret_has_256_bits_and_valid_encoding() {
        let first = generate_secret().expect("secret");
        let second = generate_secret().expect("secret");
        assert!(is_valid_secret(&first));
        assert_ne!(first, second);
    }

    #[test]
    fn validates_only_supported_axiom_urls() {
        for allowed in [
            "https://axiom.trade/meme/address?chain=sol",
            "https://axiom.trade/meme/a_B-9?chain=bsc&chains=sol,bsc",
        ] {
            assert!(validate_axiom_url(allowed).is_ok(), "{allowed}");
        }
        for rejected in [
            "http://axiom.trade/meme/address?chain=sol",
            "https://axiom.trade.evil.test/meme/address?chain=sol",
            "https://axiom.trade:444/meme/address?chain=sol",
            "https://axiom.trade/meme/address?chain=eth",
            "https://axiom.trade/meme/address?chain=sol&redirect=https://evil.test",
            "https://axiom.trade/meme/address?chain=sol#fragment",
        ] {
            assert!(validate_axiom_url(rejected).is_err(), "{rejected}");
        }
    }

    #[test]
    fn rejects_unknown_and_malformed_protocol_messages() {
        let unknown = r#"{"type":"other","protocolVersion":1}"#;
        let extra = r#"{"type":"ping","protocolVersion":1,"sentAt":"2026-09-17T10:00:00.000Z","secret":"leak"}"#;
        assert!(serde_json::from_str::<ExtensionMessage>(unknown).is_err());
        assert!(serde_json::from_str::<ExtensionMessage>(extra).is_err());
        assert!(parse_text_message(Message::Binary(b"{}".to_vec().into())).is_none());
    }

    #[test]
    fn validates_command_identifiers_and_timestamps_strictly() {
        assert!(is_uuid("123e4567-e89b-42d3-a456-426614174000"));
        assert!(!is_uuid("123e4567-e89b-02d3-a456-426614174000"));
        assert!(!is_uuid("123e4567-e89b-42d3-c456-426614174000"));

        assert!(is_iso_timestamp("2026-09-17T10:00:00.000Z"));
        assert!(is_iso_timestamp("2024-02-29T23:59:59.999Z"));
        assert!(!is_iso_timestamp("2026-02-29T10:00:00.000Z"));
        assert!(!is_iso_timestamp("2026-09-17T25:00:00.000Z"));
        assert!(!is_iso_timestamp("2026-09-17T10:00:00Z"));
    }

    #[test]
    fn navigation_commands_are_correlated_and_not_queued_twice() {
        let test_dir = std::env::temp_dir().join(format!(
            "ascend-bridge-navigation-test-{}-{}",
            std::process::id(),
            generate_secret().expect("unique suffix")
        ));
        let bridge = BridgeState::initialize(test_dir.clone()).expect("initialize bridge");
        let (sender, mut receiver) = mpsc::unbounded_channel();
        {
            let mut runtime = bridge
                .inner
                .runtime
                .lock()
                .unwrap_or_else(|error| error.into_inner());
            runtime.mode = AutoOpenMode::CurrentAxiomTab;
            runtime.connection = Some(ConnectionHandle { id: 1, sender });
        }
        let command_id = "123e4567-e89b-42d3-a456-426614174000";
        let url = "https://axiom.trade/meme/address?chain=sol";
        let issued_at = "2026-09-17T10:00:00.000Z";

        assert!(bridge.send_navigation(command_id, url, issued_at).is_ok());
        assert!(receiver.try_recv().is_ok());
        let duplicate = bridge
            .send_navigation(command_id, url, issued_at)
            .expect_err("duplicate must be rejected");
        assert_eq!(duplicate.code, "duplicate_command");

        fs::remove_file(test_dir.join(SECRET_FILE)).expect("remove test secret");
        fs::remove_dir(test_dir).expect("remove test directory");
    }

    #[test]
    fn checks_pairing_secret_without_accepting_another_value() {
        let test_dir = std::env::temp_dir().join(format!(
            "ascend-bridge-test-{}-{}",
            std::process::id(),
            generate_secret().expect("unique suffix")
        ));
        let first = BridgeState::initialize(test_dir.clone()).expect("initialize bridge");
        let secret = first
            .inner
            .secret
            .lock()
            .unwrap_or_else(|error| error.into_inner())
            .clone();
        assert!(first.matches_secret(&secret));
        assert!(!first.matches_secret(&"x".repeat(43)));

        let second = BridgeState::initialize(test_dir.clone()).expect("reload bridge");
        assert!(second.matches_secret(&secret));
        fs::remove_file(test_dir.join(SECRET_FILE)).expect("remove test secret");
        fs::remove_dir(test_dir).expect("remove test directory");
    }

    #[test]
    fn handshake_requires_exact_path_and_extension_origin() {
        fn request(path: &str, origin: &str) -> Request {
            http::Request::builder()
                .uri(path)
                .header("origin", origin)
                .body(())
                .expect("request")
        }
        fn response() -> Response {
            http::Response::builder().body(()).expect("response")
        }

        assert!(validate_handshake(&request(BRIDGE_PATH, EXTENSION_ORIGIN), response()).is_ok());
        assert!(validate_handshake(
            &request(BRIDGE_PATH, "chrome-extension://wrong"),
            response()
        )
        .is_err());
        assert!(validate_handshake(
            &request("/extension/v1?secret=forbidden", EXTENSION_ORIGIN),
            response()
        )
        .is_err());
    }

    #[test]
    fn extension_version_must_have_the_compatible_major() {
        assert!(is_compatible_extension_version("0.1.0"));
        assert!(!is_compatible_extension_version("1.0.0"));
        assert!(!is_compatible_extension_version("invalid"));
        assert!(!is_compatible_extension_version("0.1.0."));
        assert!(!is_compatible_extension_version("0.1"));
    }

    #[tokio::test]
    async fn bridge_address_is_loopback_and_occupied_port_is_detected() {
        assert_eq!(BRIDGE_ADDRESS.ip(), IpAddr::V4(Ipv4Addr::LOCALHOST));
        let listener = TcpListener::bind((Ipv4Addr::LOCALHOST, 0))
            .await
            .expect("first bind");
        let address = listener.local_addr().expect("address");
        let error = TcpListener::bind(address).await.expect_err("occupied port");
        assert_eq!(error.kind(), io::ErrorKind::AddrInUse);
    }
}
