/**
 * First-time Google OAuth flow for the SpeakPals tutor.
 * Run once on the Droplet after deploying: node gog_auth.js
 *
 * HUMAN DEPENDENCY: google_credentials.json must exist at
 * /home/openclaw/config/google_credentials.json (upload from your laptop first)
 */

const fs = require("fs");
const path = require("path");
const http = require("http");
const { execSync } = require("child_process");

const CREDENTIALS_PATH = "/home/openclaw/config/google_credentials.json";
const TOKEN_PATH = "/home/openclaw/config/google_token.json";
const REDIRECT_PORT = 8888;
const REDIRECT_URI = `http://localhost:${REDIRECT_PORT}/callback`;

const SCOPES = [
  "https://www.googleapis.com/auth/calendar",
  "https://www.googleapis.com/auth/gmail.readonly",
];

// ---------------------------------------------------------------------------
// Load credentials
// ---------------------------------------------------------------------------
if (!fs.existsSync(CREDENTIALS_PATH)) {
  console.error(`\n❌  ${CREDENTIALS_PATH} not found.`);
  console.error("Upload it from your laptop first:");
  console.error(
    `  scp C:\\path\\to\\google_credentials.json root@DROPLET_IP:${CREDENTIALS_PATH}\n`
  );
  process.exit(1);
}

const creds = JSON.parse(fs.readFileSync(CREDENTIALS_PATH, "utf8"));
const { client_id, client_secret } = creds.installed || creds.web;

// ---------------------------------------------------------------------------
// Build auth URL
// ---------------------------------------------------------------------------
const authUrl = new URL("https://accounts.google.com/o/oauth2/v2/auth");
authUrl.searchParams.set("client_id", client_id);
authUrl.searchParams.set("redirect_uri", REDIRECT_URI);
authUrl.searchParams.set("response_type", "code");
authUrl.searchParams.set("scope", SCOPES.join(" "));
authUrl.searchParams.set("access_type", "offline");
authUrl.searchParams.set("prompt", "consent");

console.log("\n🔑  Google OAuth — First-time setup");
console.log("━".repeat(50));
console.log("\nOpen this URL in your browser:\n");
console.log(authUrl.toString());
console.log("\nWaiting for OAuth callback on port", REDIRECT_PORT, "...\n");

// ---------------------------------------------------------------------------
// Local callback server
// ---------------------------------------------------------------------------
const server = http.createServer(async (req, res) => {
  const url = new URL(req.url, `http://localhost:${REDIRECT_PORT}`);
  const code = url.searchParams.get("code");

  if (!code) {
    res.writeHead(400);
    res.end("Missing code parameter.");
    return;
  }

  // Exchange code for tokens
  const tokenRes = await fetch("https://oauth2.googleapis.com/token", {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body: new URLSearchParams({
      code,
      client_id,
      client_secret,
      redirect_uri: REDIRECT_URI,
      grant_type: "authorization_code",
    }),
  });

  if (!tokenRes.ok) {
    const err = await tokenRes.text();
    res.writeHead(500);
    res.end(`Token exchange failed: ${err}`);
    console.error("❌  Token exchange failed:", err);
    server.close();
    return;
  }

  const tokenData = await tokenRes.json();
  tokenData.client_id = client_id;
  tokenData.client_secret = client_secret;
  tokenData.scopes = SCOPES;

  fs.mkdirSync(path.dirname(TOKEN_PATH), { recursive: true });
  fs.writeFileSync(TOKEN_PATH, JSON.stringify(tokenData, null, 2));

  res.writeHead(200, { "Content-Type": "text/html" });
  res.end("<h2>✅ Google account connected. You can close this tab.</h2>");

  console.log("✅  Token saved to", TOKEN_PATH);
  console.log("Google Calendar and Gmail are now connected.\n");
  server.close();
});

server.listen(REDIRECT_PORT);
