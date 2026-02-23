const crypto = require("crypto");

/**
 * Verifies GitHub webhook HMAC-SHA256 signature.
 *
 * Usage in n8n Function node:
 *   const { verifyWebhook } = require("./verify-webhook");
 *   const isValid = verifyWebhook(
 *     $input.item.json.headers["x-hub-signature-256"],
 *     JSON.stringify($input.item.json.body),
 *     $env.WEBHOOK_SECRET_CI_FAILURE
 *   );
 *
 * @param {string} signature - The x-hub-signature-256 header value
 * @param {string} payload - Raw request body as string
 * @param {string} secret - HMAC secret for this webhook
 * @returns {boolean} Whether the signature is valid
 */
function verifyWebhook(signature, payload, secret) {
  if (!signature || !payload || !secret) {
    return false;
  }

  const expected =
    "sha256=" +
    crypto.createHmac("sha256", secret).update(payload).digest("hex");

  try {
    return crypto.timingSafeEqual(
      Buffer.from(signature),
      Buffer.from(expected)
    );
  } catch {
    return false;
  }
}

module.exports = { verifyWebhook };
