class AAllBaseUrls:
   URLS = [
      #   "https://api.axiomtrade.com",
        "https://api2.axiom.trade",
        "https://api3.axiom.trade",
        # "https://api4.axiom.trade",
      #   "https://api5.axiom.trade",
        "https://api6.axiom.trade",
        "https://api7.axiom.trade",
        "https://api8.axiom.trade",
        "https://api9.axiom.trade",
        "https://api10.axiom.trade",
        # "https://api.axiom.trade",
   ]


class AxiomWssUrls:
    WSS_URL1 = "wss://cluster2.axiom.trade"


class AxiomTradeApiUrls:
    LOGIN_STEP1 = "/login-password-v2"
    LOGIN_STEP2 = "/login-otp"
    LOGOUT = "/auth/logout"
    REFRESH_TOKEN = "/refresh-access-token"
    USER_INFO = "/user/info"
    SUBSCRIBE_NEW_TOKENS = "/ws/subscribe/new-tokens"
    SUBSCRIBE_ORDERS = "/ws/subscribe/orders"
    SUBSCRIBE_POSITIONS = "/ws/subscribe/positions"
    PAIR_CHART_V2 = "/pair-chart-v2?"
    DEV_TOKENS_V3 = "/dev-tokens-v3?devAddress="
    DEV_TOKENS_V4 = "/dev-tokens-v4?devAddress="
    DEV_TOKENS_V5 = "/dev-tokens-v5?devAddress="
    TOKEN_INFO = "/token-info?pairAddress="
    PAIR_INFO = "/pair-info?pairAddress="
