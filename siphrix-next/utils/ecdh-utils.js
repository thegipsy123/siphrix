// utils/ecdh-utils.js

const ECDH_ALGO = {
  name: 'ECDH',
  namedCurve: 'P-256',
};

const AES_ALGO = {
  name: 'AES-GCM',
  length: 256,
};

export async function generateECDHKeyPair() {
  return await crypto.subtle.generateKey(ECDH_ALGO, true, ['deriveKey']);
}

export async function exportPublicKey(key) {
  const raw = await crypto.subtle.exportKey('raw', key);
  return Array.from(new Uint8Array(raw));
}

export async function importPublicKey(rawBytes) {
  return await crypto.subtle.importKey(
    'raw',
    new Uint8Array(rawBytes),
    ECDH_ALGO,
    true,
    []
  );
}

export async function deriveSharedKey(privateKey, theirPublicKey) {
  return await crypto.subtle.deriveKey(
    {
      name: 'ECDH',
      public: theirPublicKey,
    },
    privateKey,
    AES_ALGO,
    true,
    ['encrypt', 'decrypt']
  );
}
export async function importECDHKeyPair(pubJwk, privJwk) {
  const publicKey = await crypto.subtle.importKey(
    'jwk',
    pubJwk,
    ECDH_ALGO,
    true,
    []
  );

  const privateKey = await crypto.subtle.importKey(
    'jwk',
    privJwk,
    ECDH_ALGO,
    true,
    ['deriveKey']
  );

  return { publicKey, privateKey };
}
export async function exportECDHKeyPair(keyPair) {
  const publicJwk = await crypto.subtle.exportKey('jwk', keyPair.publicKey);
  const privateJwk = await crypto.subtle.exportKey('jwk', keyPair.privateKey);
  return { public: publicJwk, private: privateJwk };
}
