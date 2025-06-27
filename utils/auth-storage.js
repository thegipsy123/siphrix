const isBrowser = typeof window !== 'undefined' && 'crypto' in window && 'subtle' in window.crypto;

// ✅ Safe wrapper for subtle crypto
const subtle = isBrowser ? window.crypto.subtle : null;

// ✅ HEX helper
function toHex(buffer) {
  return [...new Uint8Array(buffer)]
    .map(b => b.toString(16).padStart(2, '0'))
    .join('');
}

// ✅ HMAC username hasher
export async function hashIdentifierWithPepper(identifier) {
  if (!subtle) throw new Error("crypto.subtle only works in the browser");

  const encoder = new TextEncoder();
  const key = await subtle.importKey(
    'raw',
    encoder.encode('SIPHRIX_SUPER_SECRET'),
    { name: 'HMAC', hash: 'SHA-256' },
    false,
    ['sign']
  );

  const signature = await subtle.sign('HMAC', key, encoder.encode(identifier));
  return toHex(signature);
}

// ✅ Save login data
export async function saveAuthData(data) {
  if (isBrowser) {
    localStorage.setItem('siphrix_auth', JSON.stringify(data));
  } else {
    const fs = await import('fs/promises');
    await fs.writeFile('user_auth.json', JSON.stringify(data, null, 2));
  }
}

// ✅ Load local backup
export async function loadAuthDataLocal() {
  if (isBrowser) {
    const raw = localStorage.getItem('siphrix_auth');
    return raw ? JSON.parse(raw) : null;
  } else {
    const fs = await import('fs/promises');
    const content = await fs.readFile('user_auth.json', 'utf-8');
    return JSON.parse(content);
  }
}

// ✅ Load vault from remote
export async function loadAuthDataRemote(username, password) {
  if (!subtle) throw new Error("crypto.subtle only works in the browser");

  const encoder = new TextEncoder();
  const key = await subtle.importKey(
    'raw',
    encoder.encode('SIPHRIX_SUPER_SECRET'),
    { name: 'HMAC', hash: 'SHA-256' },
    false,
    ['sign']
  );

  const signature = await subtle.sign('HMAC', key, encoder.encode(username));
  const hashedIdentifier = toHex(signature);

  const res = await fetch(`/userdata/${hashedIdentifier}.enc.json`);
  if (!res.ok) throw new Error('Vault not found');

  const vault = await res.json();

  const iv = new Uint8Array(vault.iv);
  const data = new Uint8Array(vault.data);
  const pbkdf2Salt = new Uint8Array(vault.pbkdf2_salt);

  const baseKey = await subtle.importKey(
    'raw',
    encoder.encode(password),
    { name: 'PBKDF2' },
    false,
    ['deriveKey']
  );

  const passwordKey = await subtle.deriveKey(
    {
      name: 'PBKDF2',
      salt: pbkdf2Salt,
      iterations: 100000,
      hash: 'SHA-256',
    },
    baseKey,
    {
      name: 'AES-GCM',
      length: 256,
    },
    false,
    ['decrypt']
  );

  const decrypted = await subtle.decrypt(
    { name: 'AES-GCM', iv },
    passwordKey,
    data
  );

  return JSON.parse(new TextDecoder().decode(decrypted));
}

// ✅ Restore backup (alternate)
export async function restoreFromVault(username, password) {
  if (!subtle) throw new Error("crypto.subtle only works in the browser");

  const hashed = await hashIdentifierWithPepper(username);
  const res = await fetch(`/userdata/${hashed}.enc.json`);
  if (!res.ok) throw new Error('Vault file not found');

  const { iv, data, pbkdf2_salt } = await res.json();

  const encoder = new TextEncoder();
  const saltBytes = new Uint8Array(pbkdf2_salt);
  const ivBytes = new Uint8Array(iv);
  const dataBytes = new Uint8Array(data);

  const baseKey = await subtle.importKey(
    'raw',
    encoder.encode(password),
    { name: 'PBKDF2' },
    false,
    ['deriveKey']
  );

  const passwordKey = await subtle.deriveKey(
    {
      name: 'PBKDF2',
      salt: saltBytes,
      iterations: 100000,
      hash: 'SHA-256',
    },
    baseKey,
    {
      name: 'AES-GCM',
      length: 256,
    },
    false,
    ['decrypt']
  );

  const decrypted = await subtle.decrypt(
    { name: 'AES-GCM', iv: ivBytes },
    passwordKey,
    dataBytes
  );

  return JSON.parse(new TextDecoder().decode(decrypted));
}
