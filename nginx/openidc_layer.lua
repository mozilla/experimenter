-- Lua reference for nginx: https://github.com/openresty/lua-nginx-module
-- Lua reference for openidc: https://github.com/pingidentity/lua-resty-openidc
local oidc = require("resty.openidc")
local cjson = require( "cjson" )

-- Load config
local f, e = loadfile(ngx.var.config_loader)
if f == nil then
  ngx.log(ngx.ERR, "can't initialize loadfile: "..e)
end
ok, e = pcall(f)
if not ok then
  ngx.log(ngx.ERR, "can't load configuration: "..e)
end

-- Authenticate with lua-resty-openidc if necessary (this will return quickly if no authentication is necessary)
local res, err, url, session = oidc.authenticate(opts)

-- Check if authentication succeeded, otherwise kick the user out
if err then
  if session ~= nil then
    session:destroy()
  end
  ngx.redirect(opts.logout_path)
else
  ngx.log(ngx.ERR, "no error was returned but session is not set. Are you using lua-resty-openidc>=1.3.2?")
end

-- Access control: only allow specific users in (this is optional, without it all authenticated users are allowed in)
-- (TODO: add example)

-- Set headers with user info and OIDC claims for the underlaying web application to use (this is optional)
-- These header names are voluntarily similar to Apaches mod_auth_openidc, but may of course be modified
ngx.req.set_header("REMOTE_USER", session.data.user.email)
ngx.req.set_header("X-Forwarded-User", session.data.user.email)
ngx.req.set_header("OIDC_CLAIM_ACCESS_TOKEN", session.data.access_token)
ngx.req.set_header("OIDC_CLAIM_ID_TOKEN", session.data.enc_id_token)
ngx.req.set_header("via",session.data.user.email)

local function build_headers(t, name)
  for k,v in pairs(t) do
    -- unpack tables
    if type(v) == "table" then
      local j = cjson.encode(v)
      ngx.req.set_header("OIDC_CLAIM_"..name..k, j)
    else
      ngx.req.set_header("OIDC_CLAIM_"..name..k, tostring(v))
    end
  end
end

build_headers(session.data.id_token, "ID_TOKEN_")
build_headers(session.data.user, "USER_PROFILE_")

-- Flat groups, useful for some RP's that won't read JSON
local gprs = ""
for k,v in pairs(session.data.user.groups) do
  grps = grps and grps.."|"..v or v
end
ngx.req.set_header("X-Forwarded-Groups", grps)
