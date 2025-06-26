import Head from 'next/head';
import { useState } from 'react';
import { useRouter } from 'next/router';
import { default as argon2 } from 'argon2-wasm-esm';


import { importECDHKeyPair } from '../utils/ecdh-utils';

export default function Login() {
  const router = useRouter();
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState('');
  const [success, setSuccess] = useState(false);



  const handleLogin = async (e) => {
    e.preventDefault();
    if (loading) return; // 🧸 Stop if already logging in
    setMessage('');
    setSuccess(false);
    setLoading(true);


    try {

       let hashedIdentifier = '';
       if (typeof window !== 'undefined') {
         const { hashIdentifierWithPepper } = await import('../utils/auth-storage.js');
         hashedIdentifier = await hashIdentifierWithPepper(username);
       } else {
         throw new Error('❌ Cannot hash identifier outside the browser');
       }

       // 🧠 Reconstruct what saveAuthData stored
        const saved = JSON.parse(localStorage.getItem(`auth_${username}`));
        if (!saved) throw new Error('❌ No saved auth data for this user');
        const { identifier, password_hash, salt } = saved;



       const vaultRaw = localStorage.getItem(`vault_${username}`);
       if (!vaultRaw) throw new Error("❌ Vault not found on this device");
       const vaultJson = JSON.parse(vaultRaw);
       if (!vaultJson) throw new Error("❌ Vault not found on this device");

       const vaultSalt = new Uint8Array(vaultJson.pbkdf2_salt);
       const iv = new Uint8Array(vaultJson.iv);
       const encryptedData = new Uint8Array(vaultJson.data);





       // 🧠 Derive AES key from password using PBKDF2 and stored salt
       const encoder = new TextEncoder();
       const baseKey = await crypto.subtle.importKey(
         'raw',
         encoder.encode(password),
         { name: 'PBKDF2' },
         false,
         ['deriveKey']
       );

       const vaultKey = await crypto.subtle.deriveKey(
         {
           name: 'PBKDF2',
           salt: vaultSalt, // ✅ Now this works fine
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


        // 🔓 Decrypt it
       const decryptedVaultBytes = await crypto.subtle.decrypt(
         { name: 'AES-GCM', iv },
         vaultKey,
         encryptedData
       );
       const decryptedVaultJson = new TextDecoder().decode(decryptedVaultBytes);
       const vault = JSON.parse(decryptedVaultJson);

       // ✅ Save profile info locally
       localStorage.setItem('siphrix_profile', JSON.stringify(vault.profile));

       if (!vault?.keys?.ecdh) {
         throw new Error("❌ Vault is missing ECDH keys.");
       }
       const { public: pubKeyJwk, private: privKeyJwk } = vault.keys.ecdh;
       const ecdhKeyPair = await importECDHKeyPair(pubKeyJwk, privKeyJwk);
       window.siphrixECDH = ecdhKeyPair; // you can also put in memory or localStorage

       if (identifier !== hashedIdentifier) {
         setMessage('❌ Invalid username');
         return;
       }

       const reHashed = await argon2.hash({
         pass: password,
         salt: new Uint8Array(salt),
       });

       const match = reHashed.encoded === password_hash;

       if (match) {

         setSuccess(true);
         setMessage('✅ Login successful!');
         const sessionData = {
         username,
         timestamp: Date.now(),
         expires: Date.now() + 100 * 24 * 60 * 60 * 1000, // 100 days in ms
        };
        localStorage.setItem('siphrix_session', JSON.stringify(sessionData));
        setTimeout(() => router.push('/chat'), 1000);
       }
       else {
         setMessage('❌ Invalid password');
       }
    } catch (err) {
      setMessage('❌ Error reading auth data');
      console.error(err);
    }
  };


  return (
    <>
      <Head>
        <title>Login – Siphrix</title>
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <style>{`
          body {
            margin: 0;
            background: #0A0C14;
            font-family: 'Inter', sans-serif;
          }

          @keyframes slideUp {
            from { opacity: 0; transform: translateY(20px); }
            to { opacity: 1; transform: translateY(0); }
          }

          @media (max-width: 480px) {
            h1 { font-size: 24px !important; }
            p  { font-size: 14px !important; }
          }

            button {
              cursor: pointer;
              height: 40px;
              padding: 0 24px;
              border-radius: 20px;
              background: linear-gradient(to right, #00E5FF, #7000FF);
              color: #FFFFFF;
              font-size: 14px;
              font-weight: 500;
              border: none;
              box-shadow: 0 0 20px rgba(0, 229, 255, 0.15);
              transition: all 0.3s ease;
            }

            button:hover {
              box-shadow: 0px 0px 60px rgba(0, 229, 255, 0.2);
              transform: translateY(-1px);
            }

        `}</style>
      </Head>

      <main style={mainStyle}>
        <div style={blurOne}></div>
        <div style={blurTwo}></div>

        <div style={boxStyle}>
          <div style={logoBox}></div>
          <h1 style={titleStyle}>Welcome Back</h1>
          <p style={subtitleStyle}>Login to your encrypted world</p>

          {message && (
            <div style={{
              marginBottom: '12px',
              color: success ? '#10B981' : '#EF4444',
              fontWeight: 'bold'
            }}>
              {message}
            </div>
          )}

          <form style={formStyle} onSubmit={handleLogin}>
            <label style={labelStyle}>Username</label>
            <input
              type="text"
              name="username"
              style={inputStyle}
              value={username}
              onChange={(e) => setUsername(e.target.value)}
            />

            <label style={labelStyle}>Password</label>
            <input
              type="password"
              name="password"
              style={inputStyle}
              value={password}
              onChange={(e) => setPassword(e.target.value)}
            />

            <button type="submit" disabled={loading}>
              {loading ? 'Logging in...' : 'Login'}
            </button>

          </form>
        </div>
      </main>
    </>
  );
}

const mainStyle = {
  height: '100vh',
  background: '#0A0C14',
  color: '#fff',
  fontFamily: 'Inter',
  display: 'flex',
  justifyContent: 'center',
  alignItems: 'center',
  position: 'relative',
  overflow: 'hidden',
};

const blurOne = {
  position: 'absolute',
  top: '10%',
  left: '10%',
  width: '400px',
  height: '400px',
  background: 'radial-gradient(circle at 50% 50%, rgba(0, 229, 255, 0.2) 0%, transparent 70%)',
  filter: 'blur(80px)',
  opacity: 0.4,
};

const blurTwo = {
  position: 'absolute',
  bottom: '10%',
  right: '10%',
  width: '500px',
  height: '500px',
  background: 'radial-gradient(circle at 50% 50%, rgba(112, 0, 255, 0.2) 0%, transparent 70%)',
  filter: 'blur(100px)',
  opacity: 0.3,
};

const boxStyle = {
  zIndex: 1,
  maxWidth: '420px',
  width: '100%',
  padding: '40px',
  borderRadius: '24px',
  background: 'linear-gradient(180deg, rgba(255,255,255,0.05) 0%, rgba(255,255,255,0.02) 100%)',
  border: '1px solid rgba(255,255,255,0.05)',
  boxShadow: '0px 0px 40px rgba(0, 229, 255, 0.1)',
  display: 'flex',
  flexDirection: 'column',
  alignItems: 'center',
  textAlign: 'center',
  animation: 'slideUp 0.8s ease forwards',
};

const logoBox = {
  width: '64px',
  height: '64px',
  background: 'rgba(255,255,255,0.03)',
  borderRadius: '16px',
  border: '1px solid rgba(255,255,255,0.05)',
  marginBottom: '24px',
  boxShadow: '0px 0px 20px rgba(0, 229, 255, 0.1)',
};

const titleStyle = {
  fontSize: '28px',
  color: '#FFFFFF',
  margin: '0 0 8px',
};

const subtitleStyle = {
  fontSize: '16px',
  color: '#B4B7C5',
  lineHeight: '24px',
  marginBottom: '24px',
};

const formStyle = {
  width: '100%',
  display: 'flex',
  flexDirection: 'column',
  gap: '12px',
};

const labelStyle = {
  textAlign: 'left',
  color: '#B4B7C5',
  fontSize: '14px',
};

const inputStyle = {
  padding: '12px',
  width: '100%',
  borderRadius: '10px',
  border: '1px solid rgba(255,255,255,0.1)',
  background: 'rgba(255,255,255,0.03)',
  color: '#fff',
};

