class AAllBaseUrls:
   URLS = [
      #   "https://api.axiomtrade.com",
        "https://api2.axiom.trade",
        "https://api3.axiom.trade",
        "https://api4.axiom.trade",
      #   "https://api5.axiom.trade",
        "https://api6.axiom.trade",
        "https://api7.axiom.trade",
        "https://api8.axiom.trade",
        "https://api9.axiom.trade",
        "https://api10.axiom.trade",
        "https://api.axiom.trade",
   ]
   
  
class AxiomTradeApiUrls:
    LOGIN_STEP1 = f"/login-password-v2"
    LOGIN_STEP2 = f"/login-otp"
    LOGOUT = f"/auth/logout"
    REFRESH_TOKEN = f"/refresh-access-token"
    USER_INFO = f"/user/info"
    SUBSCRIBE_NEW_TOKENS = f"/ws/subscribe/new-tokens"
    SUBSCRIBE_ORDERS = f"/ws/subscribe/orders"
    SUBSCRIBE_POSITIONS = f"/ws/subscribe/positions"