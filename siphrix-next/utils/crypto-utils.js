// utils/crypto-utils.js

const algorithm = {
  name: 'AES-GCM',
  length: 256,
};

const ivLength = 12; // recommended for AES-GCM

export async function generateKey() {
  return await crypto.subtle.generateKey(algorithm, true, ['encrypt', 'decrypt']);
}

export async function encryptMessage(message, key) {
  const enc = new TextEncoder();
  const iv = crypto.getRandomValues(new Uint8Array(ivLength));
  const ciphertext = await crypto.subtle.encrypt(
    { ...algorithm, iv },
    key,
    enc.encode(message)
  );

  return {
    iv: Array.from(iv),
    ciphertext: Array.from(new Uint8Array(ciphertext)),
  };
}

export async function decryptMessage({ ciphertext, iv }, key) {
  const dec = new TextDecoder();
  const plainBuffer = await crypto.subtle.decrypt(
    { ...algorithm, iv: new Uint8Array(iv) },
    key,
    new Uint8Array(ciphertext)
  );

  return dec.decode(plainBuffer);
}

export async function exportKey(key) {
  const raw = await crypto.subtle.exportKey('raw', key);
  return Array.from(new Uint8Array(raw));
}

export async function importKey(rawBytes) {
  const buffer = new Uint8Array(rawBytes);
  return await crypto.subtle.importKey('raw', buffer, algorithm, true, ['encrypt', 'decrypt']);
}
const PEPPER = 'siphrix_super_secret'; // 🔐 This MUST be the same across all devices!

export async function hashIdentifier(email) {
  const encoder = new TextEncoder();
  const key = await crypto.subtle.importKey(
    'raw',
    encoder.encode(PEPPER),
    { name: 'HMAC', hash: 'SHA-256' },
    false,
    ['sign']
  );

  const signature = await crypto.subtle.sign(
    'HMAC',
    key,
    encoder.encode(email)
  );

  return Array.from(new Uint8Array(signature))
    .map(b => b.toString(16).padStart(2, '0'))
    .join('');
}
