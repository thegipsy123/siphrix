import Head from 'next/head';
import { useState } from 'react';
import { useRouter } from 'next/router';
import { default as argon2 } from 'argon2-wasm-esm';
import { hashIdentifier } from '../utils/crypto-utils';
export default function Register() {
  const router = useRouter();
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [confirm, setConfirm] = useState('');
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState('');
  const [success, setSuccess] = useState(false);



  const handleRegister = async (e) => {
    e.preventDefault();
    setMessage('');
    setSuccess(false);

    if (password !== confirm) {
      setMessage('❌ Passwords do not match');
      return;
    }

    setLoading(true);


    let hashedIdentifier = '';
    if (typeof window !== 'undefined') {
      const { hashIdentifierWithPepper } = await import('../utils/auth-storage.js');
      hashedIdentifier = await hashIdentifierWithPepper(username);

    } else {
      throw new Error("❌ hashIdentifierWithPepper must run in the browser");
    }


    try {
      const { saveAuthData } = await import('../utils/auth-storage.js');

      const salt = crypto.getRandomValues(new Uint8Array(16));
      const hashedPassword = await argon2.hash({

        pass: password,
        salt,
      });

      // ✅ Generate ECDH key pair for encryption
      const ecdhKeyPair = await crypto.subtle.generateKey(
        { name: 'ECDH', namedCurve: 'P-256' },
        true,
        ['deriveKey']
      );

      // ✅ Export them into JSON Web Key (JWK) format
      const exportedECDHPublic = await crypto.subtle.exportKey('jwk', ecdhKeyPair.publicKey);
      const exportedECDHPrivate = await crypto.subtle.exportKey('jwk', ecdhKeyPair.privateKey);


      await saveAuthData({
        identifier: hashedIdentifier,
        password_hash: hashedPassword.encoded,
        salt: Array.from(salt),
      });

      // 🧠 1. Prepare data to store in vault
      const pbkdf2Salt = crypto.getRandomValues(new Uint8Array(16)); // 🔐 salt for AES key derivation

      const vaultData = {
        identifier: hashedIdentifier,
        password_hash: hashedPassword.encoded,
        salt: Array.from(salt),
        pbkdf2_salt: Array.from(pbkdf2Salt), // include this!
        profile: {
          name: username,
          bio: 'This is my encrypted profile 👤',
        },
        keys: {
          ecdh: {
            public: exportedECDHPublic,
            private: exportedECDHPrivate
          }
        }

      };


        // 🔐 2. Encrypt with password as AES key
      const encoder = new TextEncoder();
      const baseKey = await crypto.subtle.importKey(
        'raw',
        encoder.encode(password),
        { name: 'PBKDF2' },
        false,
        ['deriveKey']
      );

      const vaultPasswordKey = await crypto.subtle.deriveKey(
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
        ['encrypt']
      );


      const iv = crypto.getRandomValues(new Uint8Array(12));
        const vaultBytes = new TextEncoder().encode(JSON.stringify(vaultData));
        const encryptedVault = await crypto.subtle.encrypt(
          { name: 'AES-GCM', iv },
          vaultPasswordKey,
          vaultBytes
      );

        // 🌐 3. Upload to server (write to /public/userdata)
      const payload = {
        iv: Array.from(iv),
        data: Array.from(new Uint8Array(encryptedVault)),
        pbkdf2_salt: Array.from(pbkdf2Salt),
      };


      await fetch(`/api/upload-vault?user=${hashedIdentifier}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });



      setSuccess(true);
      setMessage('✅ Registration successful!');
      setTimeout(() => router.push('/login'), 1000);
    } catch (err) {
      setMessage('❌ Failed to write user file');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      <Head>
        <title>Register – Siphrix</title>
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
          <h1 style={titleStyle}>Create Account</h1>
          <p style={subtitleStyle}>Join the encrypted network</p>

          {message && (
            <div style={{
              marginBottom: '12px',
              color: success ? '#10B981' : '#EF4444',
              fontWeight: 'bold'
            }}>
              {message}
            </div>
          )}

          <form style={formStyle} onSubmit={handleRegister}>
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

            <label style={labelStyle}>Confirm Password</label>
            <input
              type="password"
              name="confirm"
              style={inputStyle}
              value={confirm}
              onChange={(e) => setConfirm(e.target.value)}
            />

            <button type="submit" style={buttonStyle} disabled={loading}>
              {loading ? 'Creating...' : 'Register'}
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

const buttonStyle = {
  cursor: 'pointer',
  height: '40px',
  padding: '0 24px',
  borderRadius: '20px',
  background: 'linear-gradient(to right, #00E5FF, #7000FF)',
  color: '#FFFFFF', // primary text color
  fontSize: '14px',
  fontWeight: 500,
  border: 'none',
  boxShadow: '0 0 20px rgba(0, 229, 255, 0.15)',
  transition: 'all 0.3s ease',
};
