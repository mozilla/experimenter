-- lua-resty-openidc options
opts = {
  redirect_uri_path = "/openid/callback/login/",
  discovery = "https://auth.mozilla.auth0.com/.well-known/openid-configuration",
  client_id = os.getenv("OPENIDC_CLIENT_ID"),
  client_secret = os.getenv("OPENIDC_CLIENT_SECRET"), 
  scope = "openid email profile",
  iat_slack = 600,
  redirect_uri_scheme = "http",
  logout_path = "/logout",
  redirect_after_logout_uri = "/",
  refresh_session_interval = 900
}
