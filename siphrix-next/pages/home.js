import Head from 'next/head';
import { useRouter } from 'next/router';

export default function Home() {
  const router = useRouter();

  return (
    <>
      <Head>
        <title>Welcome to Siphrix 🔐</title>
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <link href="https://fonts.googleapis.com/css2?family=Inter&display=swap" rel="stylesheet" />
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

  @media (max-width: 480px) {
    h1 { font-size: 24px !important; }
    p  { font-size: 14px !important; }
  }
`}</style>


      </Head>

      <div style={containerStyle}>
        {<>
  {/* Glowing background blur */}
  <div style={blurOne}></div>
  <div style={blurTwo}></div>

  {/* Glassy Welcome Box */}
  <div style={boxStyle}>
    <div style={logoBox}></div>
    <h1 style={titleStyle}>Welcome to Siphrix</h1>
    <p style={subtitleStyle}>Secure messaging for the modern world</p>
    <div style={buttonGroup}>
  <button onClick={() => router.push('/register')}>Create Account</button>
  <button onClick={() => router.push('/login')}>Login</button>
</div>

  </div>
</>
}
      </div>
    </>
  );
}

const containerStyle = {
  display: 'flex',
  justifyContent: 'center',
  alignItems: 'center',
  minHeight: '100vh',
  padding: '20px',
  position: 'relative',
  overflow: 'hidden',
  backgroundColor: '#0A0C14',
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
  fontSize: '32px',
  color: '#FFFFFF',
  margin: '0 0 12px',
};

const subtitleStyle = {
  fontSize: '16px',
  color: '#B4B7C5',
  lineHeight: '24px',
  marginBottom: '30px',
};

const buttonGroup = {
  display: 'flex',
  flexDirection: 'column',
  gap: '12px',
  width: '100%',
};

// ✨ Add this for animations & responsiveness
const globalAnimationStyles = `
  @keyframes slideUp {
    from {
      opacity: 0;
      transform: translateY(20px);
    }
    to {
      opacity: 1;
      transform: translateY(0);
    }
  }

  @media (max-width: 480px) {
    h1 {
      font-size: 24px !important;
    }
    p {
      font-size: 14px !important;
    }
  }
`;

