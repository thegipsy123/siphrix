import Head from 'next/head';
import { useState } from 'react';
import { useRouter } from 'next/router';

export default function HomePage() {
  const router = useRouter();
  const [isLoggedIn, setIsLoggedIn] = useState(false); // Fake login state

  return (
    <>
      <Head>
          <title>Siphrix Landing Page</title>
          <meta name="viewport" content="width=device-width, initial-scale=1" />
      </Head>

      {/* ✅ Navigation Section */}
<div className="nav">
  <div className="nav-container">
    {/* Nav Left */}
    <div className="nav-left">
      <div className="logo">🛡️ Siphrix</div>
      <div className="nav-links">
        <a href="#features">Features</a>
        <a href="#security">Security</a>
        <a href="#about">About</a>
      </div>
    </div>

    {/* Nav Right */}
    <div className="nav-right">
      <button onClick={() => router.push('/login')}>Login</button>


      <button onClick={() => router.push('/register')}>Signup</button>


    </div>
  </div>
</div>


      <main className="main-section">
         <div className="hero-container">
          <div className="hero-left">
            <h1 className="hero-title">Secure Messaging for the Digital Age</h1>
            <p className="hero-subtitle">
              Protect your conversations with military-grade encryption. Communicate freely, knowing your privacy is our priority.
            </p>
            <div className="hero-cta">
              <button className="hero-cta-button" onClick={() => router.push('/home')}>Start Secure Chat</button>
              <a className="hero-demo-link" onClick={() => alert("🎥 Demo coming soon!")}>Watch Demo</a>
            </div>
          </div>

          <div className="hero-right">
            <img
              className="hero-image"
              src="https://images.unsplash.com/photo-1633265486064-086b219458ec?q=80&w=1200"
              alt="Secure App UI"
            />
            <div className="hero-cards">
              <div className="hero-card">
                🔐 <strong>End-to-End Encryption</strong><br />
                <small>Military-grade encryption protects every message.</small>
              </div>
              <div className="hero-card">
                ⚡ <strong>Lightning Fast</strong><br />
                <small>Instant messaging without compromising security.</small>
              </div>
              <div className="hero-card">
                🛡️ <strong>Zero Knowledge</strong><br />
                <small>We never access or store your private conversations.</small>
              </div>
            </div>
          </div>
        </div>

      </main>




      <style jsx>{`
        .nav {
          position: fixed;
          top: 0;
          width: 100%;
          height: 80px;
          z-index: 100;
          background: rgba(10, 12, 20, 0.8);
          backdrop-filter: blur(20px);
          border-bottom: 1px solid rgba(255, 255, 255, 0.05);
          display: flex;
          justify-content: center;
        }

        .nav-container {
          height: 100%;
          max-width: 1400px;
          margin: 0 auto;
          padding: 0 24px;
          width: 100%;
          display: flex;
          align-items: center;
          justify-content: space-between;
        }

        .nav-left {
          display: flex;
          align-items: center;
          gap: 48px;
        }

        .logo {
          font-weight: bold;
          color: white;
          font-size: 18px;
        }

        .nav-links {
          display: flex;
          gap: 32px;
        }

        .nav-links a {
          font-size: 14px;
          color: #B4B7C5;
          text-decoration: none;
          cursor: pointer;
          transition: all 0.3s ease;
        }

        .nav-links a:hover {
          color: #00E5FF;
        }

        .nav-right {
          display: flex;
          align-items: center;
          gap: 16px;
        }

        .nav-right button {
          height: 40px;
          padding: 0 24px;
          font-size: 14px;
          border-radius: 20px;
          transition: all 0.3s ease;
        }

        /* 🧊 Login Button — glass effect */
        .nav-right button:first-child {
          background-color: rgba(255, 255, 255, 0.02);
          color: white;
          border: 1px solid rgba(255, 255, 255, 0.05);
        }
        .nav-right button:first-child:hover {
          transform: translateY(-1px);
          background-color: rgba(255, 255, 255, 0.05);
        }

        /* 🌈 Signup Button — gradient glow */
        .nav-right button:last-child {
          background: linear-gradient(135deg, #00E5FF, #7000FF);
          color: white;
          border: none;
        }
        .nav-right button:last-child:hover {
          transform: translateY(-1px);
          box-shadow: 0px 0px 60px rgba(0, 229, 255, 0.2);
        }


        .logo {
          font-weight: bold;
          color: white;
          font-size: 18px;
        }



        .nav-links a:hover {
          color: #00ccff;
        }

        .main {
          padding-top: 100px;
          min-height: 100vh;
          background: linear-gradient(to bottom, #121212, #1a1a1a);
          display: flex;
          justify-content: center;
          align-items: center;
        }
        .hero {
          display: flex;
          max-width: 1200px;
          padding: 40px;
          gap: 40px;
          flex-wrap: wrap;
        }
        .hero-left {
          flex: 1;
        }
        .hero-left h1 {
          font-size: 40px;
          margin-bottom: 10px;
        }
        .hero-left p {
          font-size: 18px;
          color: #aaa;
          margin-bottom: 20px;
        }
        .cta {
          display: flex;
          align-items: center;
          gap: 20px;
        }
        .cta button {
          padding: 12px 24px;
          font-size: 16px;
          border-radius: 8px;
          border: none;
          background: #00cc88;
          color: black;
          font-weight: bold;
          cursor: pointer;
        }
        .cta a {
          color: #00ccff;
          text-decoration: underline;
          cursor: pointer;
        }
        .hero-right {
          flex: 1;
          display: flex;
          flex-direction: column;
          align-items: center;
          gap: 20px;
        }
        .hero-image {
          width: 100%;
          max-width: 400px;
          height: 250px;
          background-image: url('https://via.placeholder.com/400x250.png?text=Hero+Image');
          background-size: cover;
          background-position: center;
          border-radius: 16px;
          box-shadow: 0 4px 20px rgba(0, 0, 0, 0.6);
        }
        .card {
          background: #222;
          padding: 20px;
          border-radius: 12px;
          width: 100%;
          max-width: 400px;
          box-shadow: 0 0 10px #00cc88;
        }
        @media (max-width: 768px) {
          .hero {
            flex-direction: column;
            align-items: center;
          }
          .hero-right {
            align-items: center;
          }
        }

        .main-section {
          display: block;
          padding: 80px 0 0 0;
          min-height: 100vh;
          background: #0A0C14; /* Replace with: variables['Theme'].colors.background if needed */
        }

        .hero-container {
          margin: 0 auto;
          display: flex;
          flex-wrap: wrap;
          padding: 120px 24px 0 24px;
          max-width: 1400px;
          row-gap: 48px;
          column-gap: 48px;
          align-items: center;
          justify-content: space-between;
          width: 100%;
        }
        .hero-left {
          flex: 1;
          display: flex;
          flex-direction: column;
          gap: 32px;
          max-width: 600px;
        }

        .hero-title {
          font-size: 56px;
          font-weight: 700;
          line-height: 1.2;
          color: white;
          animation: fadeIn 1s ease-out 0.2s both;
        }

        .hero-subtitle {
          font-size: 18px;
          font-weight: 400;
          line-height: 1.6;
          color: #B4B7C5;
          opacity: 0.8;
          animation: slideUp 0.8s ease-out 0.4s both;
        }

        .hero-cta {
          display: flex;
          align-items: center;
          gap: 24px;
          animation: slideUp 0.8s ease-out 0.6s both;
        }

        .hero-cta-button {
          height: 56px;
          padding: 0 32px;
          background: linear-gradient(135deg, #00E5FF, #7000FF);
          color: white;
          border: none;
          border-radius: 28px;
          font-size: 16px;
          font-weight: 600;
          box-shadow: 0 10px 30px rgba(0, 229, 255, 0.3);
          cursor: pointer;
          transition: all 0.3s ease;
        }
        .hero-cta-button:hover {
          transform: scale(1.05);
          box-shadow: 0 15px 40px rgba(0, 229, 255, 0.4);
        }

        .hero-demo-link {
          font-size: 16px;
          text-decoration: underline;
          color: #00E5FF;
          cursor: pointer;
          transition: all 0.3s ease;
        }
        .hero-demo-link:hover {
          text-decoration: none;
          color: #4DFFFF;
        }

        .hero-right {
          flex: 1;
          display: flex;
          flex-direction: column;
          gap: 24px;
          position: relative;
          min-height: 600px;
        }

        .hero-image {
          width: 100%;
          max-width: 600px;
          height: auto;
          border-radius: 24px;
          box-shadow: 0 30px 60px rgba(0, 0, 0, 0.2);
          border: 2px solid rgba(255, 255, 255, 0.1);
          transition: transform 0.5s ease;
        }
        .hero-image:hover {
          transform: scale(1.02);
        }

        .hero-cards {
          display: flex;
          gap: 24px;
          margin-top: 32px;
          flex-wrap: wrap;
        }
        .hero-card {
          background: rgba(10, 12, 20, 0.5);
          border: 1px solid rgba(255, 255, 255, 0.1);
          border-radius: 12px;
          padding: 24px;
          width: 100%;
          max-width: 180px;
          backdrop-filter: blur(10px);
          color: white;
          font-size: 14px;
          line-height: 1.4;
          box-shadow: 0 10px 20px rgba(0, 0, 0, 0.2);
        }

        @keyframes fadeIn {
          from { opacity: 0; transform: translateY(20px); }
          to { opacity: 1; transform: translateY(0); }
        }
        @keyframes slideUp {
          from { opacity: 0; transform: translateY(40px); }
          to { opacity: 1; transform: translateY(0); }
        }
        .modal {
          position: fixed;
          inset: 0;
          background: rgba(0, 0, 0, 0.5);
          backdrop-filter: blur(8px);
          display: flex;
          justify-content: center;
          align-items: center;
          z-index: 999;
        }
        .modal-box {
          width: 480px;
          background: rgba(10, 12, 20, 0.9);
          border-radius: 16px;
          box-shadow: 0 30px 60px rgba(0, 0, 0, 0.2);
          padding: 32px;
          display: flex;
          flex-direction: column;
          gap: 16px;
        }
        .modal-box h2 {
          color: white;
        }
        .modal-box input {
          padding: 12px;
          border-radius: 8px;
          border: none;
          font-size: 14px;
        }
        .modal-box button {
          height: 40px;
          border-radius: 20px;
          background: linear-gradient(135deg, #00E5FF, #7000FF);
          color: white;
          font-weight: bold;
          border: none;
          cursor: pointer;
        }
        .modal-box button:hover {
          transform: translateY(-1px);
          box-shadow: 0 0 30px rgba(0, 229, 255, 0.2);
        }

      `}</style>
    </>
  );
}
