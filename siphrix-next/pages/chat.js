async function hashUsername(username) {
  const encoded = new TextEncoder().encode(username);
  const hashBuffer = await crypto.subtle.digest("SHA-256", encoded);
  return Array.from(new Uint8Array(hashBuffer))
    .map(b => b.toString(16).padStart(2, '0')).join('');
}

async function encryptWithPublicKey(message, pem) {
  const encoder = new TextEncoder();
  const key = await window.crypto.subtle.importKey(
    "spki",
    str2ab(atob(pem.replace(/-----.*?-----/g, "").replace(/\s+/g, ''))),
    { name: "RSA-OAEP", hash: "SHA-256" },
    false,
    ["encrypt"]
  );
  const data = encoder.encode(message);
  const encrypted = await window.crypto.subtle.encrypt({ name: "RSA-OAEP" }, key, data);
  return btoa(String.fromCharCode(...new Uint8Array(encrypted)));
}

function str2ab(str) {
  const binary = atob(str);
  const len = binary.length;
  const bytes = new Uint8Array(len);
  for (let i = 0; i < len; i++) {
    bytes[i] = binary.charCodeAt(i);
  }
  return bytes.buffer;
}


import Head from 'next/head';
import { useState, useEffect, useRef } from 'react';
import { useRouter } from 'next/router';
import {
  initConnection,
  connectToOffer,
  completeConnection,
  sendMessage as sendPeerMessage
} from '../utils/peer_connection';

import {
  generateKey,
  encryptMessage,
  decryptMessage,
} from '../utils/crypto-utils';
import {
  generateECDHKeyPair,
  exportPublicKey,
  importPublicKey,
  deriveSharedKey,
} from '../utils/ecdh-utils';

const publicKeys = {};

async function sha256Hex(str) {
  const encoder = new TextEncoder();
  const data = encoder.encode(str);
  const hashBuffer = await crypto.subtle.digest('SHA-256', data);
  return Array.from(new Uint8Array(hashBuffer)).map(b => b.toString(16).padStart(2, '0')).join('');
}


export default function Chat() {
  const router = useRouter(); // 👈 ADD THIS
  const messagesEndRef = useRef(null);
  const [profile, setProfile] = useState({ name: '', bio: '' });

  // ✅ Check if session exists
  useEffect(() => {
    const savedProfile = localStorage.getItem('siphrix_profile');
    if (savedProfile) {
      setProfile(JSON.parse(savedProfile));
    }

    const session = localStorage.getItem('siphrix_session');
    if (!session) {
      router.push('/login');
    }
  }, []);



  const contacts = [
  {
    name: 'Alice',
    status: 'Online',
    avatar: 'https://randomuser.me/api/portraits/women/1.jpg',
    time: '2 min ago',
    online: true,
  },
  {
    name: 'Bob',
    status: 'Away',
    avatar: 'https://randomuser.me/api/portraits/men/2.jpg',
    time: '5 min ago',
    online: false,
  },
  {
    name: 'Carol',
    status: 'Busy',
    avatar: 'https://randomuser.me/api/portraits/women/3.jpg',
    time: 'now',
    online: true,
  },
  {
    name: 'David',
    status: 'Offline',
    avatar: 'https://randomuser.me/api/portraits/men/4.jpg',
    time: '1 hour ago',
    online: false,
  },
];

function makeId() {
  return Math.random().toString(36).substring(2, 10);
}

  const [messages, setMessages] = useState([
  { text: 'Hey, are you there?', sender: 'them' },
  { text: "Yes! I'm working on Siphrix 🔐", sender: 'me' },
]);

// 👇 Auto scroll to bottom when messages change
    useEffect(() => {
      messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [messages]);


const [input, setInput] = useState('');
const [selected, setSelected] = useState(0);
const [sidebarOpen, setSidebarOpen] = useState(true);
const [selectedNav, setSelectedNav] = useState('contacts');
const [showDrawer, setShowDrawer] = useState(false);
const [searchTerm, setSearchTerm] = useState('');
const filteredContacts = contacts.filter(c =>
  c.name.toLowerCase().includes(searchTerm.toLowerCase())
);
const filteredMessages = messages.filter(m =>
  m.text?.toLowerCase().includes(searchTerm.toLowerCase())
);

const [aesKey, setAesKey] = useState(null);
const [myECDHKeys, setMyECDHKeys] = useState(null);
const [sharedKeys, setSharedKeys] = useState({}); // AES keys per contact
const [pendingFile, setPendingFile] = useState(null);
const [deliveredIds, setDeliveredIds] = useState([]);

function panicWipe() {
  setMessages([]);
  setSharedKeys({});
  setAesKey(null);
  setMyECDHKeys(null);
  alert('🧨 All messages and keys wiped!');
}



useEffect(() => {

  const sessionRaw = localStorage.getItem('siphrix_session');
   if (!sessionRaw) {
     router.push('/login');
     return;
   }
  const session = JSON.parse(sessionRaw);
   if (Date.now() > session.expires) {
     localStorage.removeItem('siphrix_session');
     router.push('/login');
     return;
   }

  const savedOffer = localStorage.getItem('webrtc_offer');
  const savedAnswer = localStorage.getItem('webrtc_answer');

  async function setupP2P() {
    if (!savedOffer && !savedAnswer) {
      const offer = await initConnection(handlePeerMessage);
      localStorage.setItem('webrtc_offer', offer);
      alert("📤 Share this offer with your peer:\n\n" + offer);
    } else if (savedOffer && !savedAnswer) {
      const answer = prompt("📥 Paste the answer SDP:");
      if (answer) {
        await completeConnection(answer);
        localStorage.setItem('webrtc_answer', answer);
        alert("✅ Connection established!");
      }
    } else if (!savedOffer && savedAnswer) {
      const offer = prompt("📥 Paste the offer SDP:");
      const answer = await connectToOffer(offer, handlePeerMessage);
      localStorage.setItem('webrtc_answer', answer);
      alert("✅ Answer sent. You are connected!");
    }
  }

  function handlePeerMessage(data) {
  try {
    const parsed = JSON.parse(data);
    if (parsed.type === 'file' && parsed.metadata) {
      const blob = new Blob(
        [Uint8Array.from(parsed.metadata.encrypted.ciphertext)],
        { type: parsed.metadata.type }
      );
      const url = URL.createObjectURL(blob);

      setMessages(prev => [...prev, {
        file: true,
        name: parsed.metadata.name,
        type: parsed.metadata.type,
        url,
        sender: 'them',
      }]);
      return;
    }
  } catch {}

  // If not a file message, treat as normal text:
  setMessages(prev => [...prev, { text: data, sender: 'them' }]);
}


  setupP2P();
}, []);





async function decryptText(msgText) {
  if (!aesKey) return '[key missing]';

  try {
    const encrypted = JSON.parse(msgText);
    const decrypted = await decryptMessage(encrypted, aesKey);
    return decrypted;
  } catch (err) {
    return '[decryption error]';
  }
}

const handleSend = async () => {
  if (!input.trim()) return;

  const plainText = input.trim();
  const recipient = contacts[selected].name;

  // Try fetch key from local first
  if (!publicKeys[recipient]) {
    const hashed = await hashUsername(recipient);
    const dhtData = await fetch(`/userdata/${hashed}.json`).then(res => res.json()).catch(() => null);
    if (dhtData && dhtData.public_key) {
      publicKeys[recipient] = dhtData.public_key;
    } else {
      alert("❌ Recipient not found in DHT.");
      return;
    }
  }

  const route = await fetch(`/api/route?to=${recipient}`).then(res => res.json());
  let encrypted = plainText;

  for (let i = route.length - 1; i >= 0; i--) {
    const hopKey = publicKeys[route[i]];
    encrypted = await encryptWithPublicKey(encrypted, hopKey);
  }

  const payload = {
    type: "onion",
    route: route.slice(1),
    payload: encrypted,
  };

  const outer = await encryptWithPublicKey(JSON.stringify(payload), publicKeys[route[0]]);

  sendPeerMessage(JSON.stringify({
    type: "onion",
    route: [route[0]],
    payload: outer
  }));

  setMessages(prev => [...prev, {
    text: plainText,
    sender: 'me',
    status: 'sent',
  }]);

  setInput('');
};



async function handleFileUpload(e) {
  const file = e.target.files[0];
  if (!file) return;

  const friend = contacts[selected].name;
  const contactKey = sharedKeys[friend];
  if (!contactKey) return alert("No shared key for this contact");

  const arrayBuffer = await file.arrayBuffer();
  const encrypted = await encryptMessage(arrayBuffer, contactKey);

  const metadata = {
    name: file.name,
    type: file.type,
    size: file.size,
    encrypted,
  };

sendPeerMessage(JSON.stringify({
  type: 'file',
  metadata
}));

  const blob = new Blob([arrayBuffer], { type: file.type });
  const url = URL.createObjectURL(blob);

  setMessages((prev) => [
    ...prev,
    {
      file: true,
      name: file.name,
      type: file.type,
      url,
      sender: 'me',
    },
  ]);

  setPendingFile(null); // clear preview
}

function Decryptor({ text }) {
  const [plain, setPlain] = useState('🔐');

  useEffect(() => {
    decryptText(text).then(setPlain);
  }, [text]);

  return <>{plain}</>;
}

function getKeyStatus() {
  const friend = contacts[selected].name;
  const hasKey = !!sharedKeys[friend];
  return hasKey ? `🔐 Secure with ${friend}` : `❌ Not encrypted`;
}

  return (
    <>
      <Head>
        <title>Siphrix Chat</title>
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <link href="https://fonts.googleapis.com/css2?family=Inter&display=swap" rel="stylesheet" />
        <style>{`
          html, body {
            margin: 0;
            padding: 0;
            background: #0A0C14;
            font-family: 'Inter', sans-serif;
            height: 100%;
            overflow: hidden;
          }


          .layout {
            display: flex;
            flex: 1;
            lex-direction: row;
            height: calc(100vh - 60px); /* ✅ this subtracts the topbar height */
            overflow: hidden;
          }


          .sidebar {
  width: 280px;
  background: rgba(17, 19, 26, 0.6);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border-right: 1px solid rgba(255,255,255,0.05);
  display: flex;
  flex-direction: column;
  transition: transform 0.3s ease;
  z-index: 5;
}


          .sidebar.closed {
            transform: translateX(-100%);
          }

          .topbar {
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  background: #0A0C14;
  padding: 0 16px;
  border-bottom: 1px solid rgba(255,255,255,0.05);
  position: relative;
  z-index: 10;
}

          .topbar h1 {
            font-size: 18px;
            color: white;
          }

          .topbar input {
            background: rgba(255,255,255,0.05);
            border: none;
            border-radius: 8px;
            padding: 8px;
            color: white;
            margin: 0 12px;
            width: 200px;
          }

          .contact-list {
            flex: 1;
            overflow-y: auto;
            padding: 10px;
          }

          .contact {
            display: flex;
            align-items: center;
            gap: 10px;
            padding: 10px;
            border-radius: 12px;
            cursor: pointer;
            transition: background 0.2s ease;
          }
          .contact.selected {
  background: rgba(0, 229, 255, 0.1);
  border: 1px solid #00E5FF;
}


          .contact:hover {
            background: rgba(255,255,255,0.05);
          }

          .avatar {
            width: 36px;
            height: 36px;
            border-radius: 50%;
            position: relative;
          }

          .dot {
            position: absolute;
            bottom: 0;
            right: 0;
            width: 10px;
            height: 10px;
            border-radius: 50%;
            border: 2px solid #11131a;
          }

          .main {
            flex: 1;
            display: flex;
            flex-direction: column;
            background: #0A0C14;
            position: relative;
            min-height: 0;
            overflow: hidden;
          }


          .chat-header {
            display: flex;
            align-items: center;
            padding: 16px;
            gap: 12px;
            background: #11131a;
            border-bottom: 1px solid rgba(255,255,255,0.05);
          }

          .chat-avatar {
            width: 40px;
            height: 40px;
            border-radius: 50%;
            background: #5e9aff;
          }

          .pinned {
            background: #1e1f26;
            padding: 8px 16px;
            font-size: 13px;
            color: #ccc;
            border-bottom: 1px solid rgba(255,255,255,0.05);
            position: sticky;
            top: 0;
            z-index: 2;
          }

          .messages {
            flex: 1;
            min-height: 0;
            overflow-y: auto;
            padding: 20px;
            display: flex;
            flex-direction: column;
            gap: 10px;
          }



          .bubble {
  max-width: 60%;
  padding: 12px 16px;
  border-radius: 18px;
  font-size: 14px;
  line-height: 1.6;
  animation: fadeIn 0.25s ease;
  word-break: break-word;
  white-space: pre-wrap;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.1);
  transition: transform 0.2s ease;
}

.bubble:hover {
  transform: scale(1.02);
}

.incoming {
  background: rgba(255,255,255,0.05);
  align-self: flex-start;
  color: #fff;
  border-radius: 16px 16px 16px 4px;
}

.outgoing {
  background: #00E5FF;
  align-self: flex-end;
  color: #000;
  border-radius: 16px 16px 4px 16px;
}

          .input-bar {
            display: flex;
            padding: 16px;
            background: #11131a;
            border-top: 1px solid rgba(255,255,255,0.05);
          }

          .input-bar input {
  flex: 1;
  padding: 12px;
  border-radius: 10px;
  border: 1px solid rgba(255,255,255,0.1);
  background: rgba(255,255,255,0.03);
  color: white;
  margin: 0 10px;
}


          .input-bar button {
  background: #00E5FF;
  color: black;
  font-weight: bold;
  padding: 12px 20px;
  border: none;
  border-radius: 10px;
  margin-left: 10px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.input-bar button:hover {
  background: #00bddd;
}


          .hamburger {
            font-size: 24px;
            background: none;
            color: white;
            border: none;
            cursor: pointer;
          }
          .icon {
  background: transparent;
  color: #ccc;
  border: none;
  font-size: 20px;
  margin-right: 10px;
  cursor: pointer;
}
.icon:hover {
  color: #00E5FF;
}
.bubble:hover {
  filter: brightness(1.1);
}
.glow-blur {
  position: fixed;
  width: 500px;
  height: 500px;
  background: radial-gradient(circle at center, rgba(0, 229, 255, 0.15), transparent 70%);
  filter: blur(120px);
  z-index: 0;
  pointer-events: none;
}

.glow-left {
  top: 20%;
  left: -100px;
}

.glow-right {
  bottom: 10%;
  right: -100px;
  background: radial-gradient(circle at center, rgba(112, 0, 255, 0.12), transparent 70%);
}
.settings-icon {
  font-size: 20px;
  cursor: pointer;
  background: transparent;
  border: none;
  color: #ccc;
  transition: transform 0.2s ease;
}

.settings-icon:hover {
  transform: rotate(90deg);
  color: #00E5FF;
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(8px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.nav-rail {
  width: 60px;
  background: rgba(17, 19, 26, 0.6);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border-right: 1px solid rgba(255,255,255,0.05);
  display: flex;
  flex-direction: column;
  align-items: center;
  padding-top: 16px;
  gap: 16px;
}

.nav-btn {
  background: transparent;
  color: #ccc;
  border: none;
  font-size: 20px;
  padding: 10px;
  border-radius: 10px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.nav-btn:hover {
  color: #00E5FF;
}

.nav-btn.active {
  background: rgba(0, 229, 255, 0.1);
  border: 1px solid #00E5FF;
  color: #00E5FF;
}
.avatar-wrap {
  position: relative;
  width: 40px;
  height: 40px;
  border-radius: 50%;
  overflow: hidden;
  flex-shrink: 0;
}

.avatar-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  border-radius: 50%;
}
.topbar-center {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 2px;
}

.chat-title {
  font-size: 16px;
  font-weight: bold;
  color: #fff;
}

.chat-badge {
  background: rgba(0, 229, 255, 0.1);
  color: #00E5FF;
  font-size: 11px;
  padding: 2px 8px;
  border-radius: 6px;
  font-weight: 500;
}

.topbar-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

.action-icon {
  background: rgba(255, 255, 255, 0.05);
  border: none;
  color: #ccc;
  font-size: 16px;
  padding: 8px;
  border-radius: 8px;
  cursor: pointer;
  transition: background 0.2s ease;
}

.action-icon:hover {
  background: rgba(0, 229, 255, 0.2);
  color: #00E5FF;
}
.drawer {
  position: fixed;
  top: 0;
  left: 0;
  width: 280px;
  height: 100%;
  background: rgba(17, 19, 26, 0.9);
  backdrop-filter: blur(24px);
  -webkit-backdrop-filter: blur(24px);
  color: #fff;
  padding: 20px;
  z-index: 999;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.drawer-header {
  display: flex;
  justify-content: space-between;
  font-weight: bold;
  font-size: 16px;
}

.close-btn {
  background: transparent;
  border: none;
  color: #ccc;
  font-size: 18px;
  cursor: pointer;
}

.profile-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  gap: 6px;
}

.profile-pic {
  width: 72px;
  height: 72px;
  border-radius: 50%;
  border: 3px solid #00E5FF;
}

.profile-name {
  font-size: 16px;
  font-weight: bold;
}

.profile-status {
  color: #00FFAA;
  font-size: 13px;
}

.profile-bio {
  font-size: 13px;
  color: #aaa;
}

.drawer-section {
  display: flex;
  flex-direction: column;
  gap: 10px;
  margin-top: 20px;
}

.drawer-btn {
  background: rgba(255,255,255,0.05);
  color: #ccc;
  border: none;
  padding: 10px 12px;
  border-radius: 10px;
  text-align: left;
  cursor: pointer;
  transition: background 0.2s ease;
}

.drawer-btn:hover {
  background: rgba(0, 229, 255, 0.15);
  color: #00E5FF;
}

.drawer-btn.danger {
  background: rgba(255,0,0,0.1);
  color: #f55;
  font-weight: bold;
}

.drawer-btn.danger:hover {
  background: rgba(255,0,0,0.2);
  color: #fff;
}

@media (max-width: 768px) {
  .layout {
    flex-direction: column;
  }

  .nav-rail {
    flex-direction: row;
    justify-content: space-around;
    width: 100%;
    height: 60px;
    padding: 8px;
    position: fixed;
    bottom: 0;
    z-index: 10;
    border-top: 1px solid rgba(255,255,255,0.1);
  }

  .sidebar {
    display: none;
  }

  .main {
    padding-bottom: 60px; /* make room for mobile nav */
  }

  .input-bar {
    position: fixed;
    bottom: 60px;
    width: 100%;
    left: 0;
    border-top: 1px solid rgba(255,255,255,0.05);
    padding: 12px;
    background: #11131a;
    z-index: 10;
  }

  .topbar {
    flex-wrap: wrap;
    gap: 4px;
  }

  .topbar-center {
    flex-direction: column;
    align-items: flex-start;
    text-align: left;
  }

  .chat-title {
    font-size: 15px;
  }

  .chat-badge {
    font-size: 10px;
  }

  .drawer {
    width: 100%;
  }
}

.drawer {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.5);
  z-index: 999;
  display: flex;
  justify-content: flex-start;
  align-items: stretch;
}

.drawer-sheet {
  width: 300px;
  height: 100%;
  background: rgba(21, 24, 37, 0.95);
  padding: 32px 24px;
  display: flex;
  flex-direction: column;
}

.drawer-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}

.drawer-title {
  font-size: 24px;
  font-weight: 600;
  color: #fff;
}

.drawer-close {
  font-size: 20px;
  background: rgba(255, 255, 255, 0.05);
  border: none;
  border-radius: 6px;
  color: #fff;
  padding: 6px 10px;
  cursor: pointer;
}

.drawer-close:hover {
  background: rgba(255, 255, 255, 0.1);
}

.drawer-section {
  display: flex;
  flex-direction: column;
  gap: 10px;
  margin-top: auto;
}

.drawer-btn {
  background: rgba(255, 255, 255, 0.05);
  color: #ccc;
  border: none;
  padding: 10px 14px;
  border-radius: 10px;
  text-align: left;
  font-size: 14px;
  cursor: pointer;
  transition: background 0.2s ease;
}

.drawer-btn:hover {
  background: rgba(255, 255, 255, 0.1);
  color: #fff;
}

.drawer-btn.danger {
  background: rgba(255, 0, 0, 0.15);
  color: #f55;
}

.drawer-btn.danger:hover {
  background: rgba(255, 0, 0, 0.25);
  color: #fff;
}

.profile-section {
  width: 100%;
  display: flex;
  flex-direction: column;
  gap: 20px;
  padding: 24px;
  border-radius: 16px;
  background: rgba(255, 255, 255, 0.03);
  position: relative;
}

.avatar-container {
  display: flex;
  justify-content: center;
  width: 100%;
}

.profile-avatar {
  width: 120px;
  height: 120px;
  border: 3px solid #00E5FF;
  box-shadow: 0 0 30px rgba(0, 229, 255, 0.2);
  border-radius: 100%;
}

.profile-info {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.profile-name {
  font-size: 24px;
  font-weight: 600;
  color: #FFFFFF;
}

.online-status {
  font-size: 16px;
}

.last-seen {
  font-size: 14px;
  color: #636879;
}

.bio-box {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.bio-label {
  font-size: 14px;
  color: #636879;
}

.bio-text {
  font-size: 14px;
  color: #FFFFFF;
}

.search-bar {
  background: rgba(255, 255, 255, 0.05);
  border: none;
  border-radius: 8px;
  padding: 8px 12px;
  color: white;
  margin-left: 12px;
  font-size: 14px;
  flex-shrink: 0;
  width: 180px;
}
.search-bar::placeholder {
  color: #999;
}


        `}</style>
      </Head>
      {/* Glowing Backgrounds */}
<div className="glow-blur glow-left"></div>
<div className="glow-blur glow-right"></div>


      <div className="topbar">
  <button className="hamburger" onClick={() => setShowDrawer(true)}>☰</button>
  <input
    type="text"
    placeholder="Search..."
    value={searchTerm}
    onChange={(e) => setSearchTerm(e.target.value)}
    style={{
      background: 'rgba(255,255,255,0.05)',
      border: 'none',
      borderRadius: '8px',
      padding: '8px',
      color: 'white',
      marginLeft: '12px',
      width: '200px'
    }}
  />


  <div className="topbar-center">
    <span className="chat-title">Secure Chat</span>
    <span className="chat-badge">🔒 End-to-End Encrypted</span>
  </div>

  <div className="topbar-actions">
    <button className="action-icon">📹</button>
    <button className="action-icon">📞</button>
    <button className="action-icon">⚠️</button>
  </div>
</div>


      <div className="layout">
      <div className="nav-rail">
 <button className={`nav-btn ${selectedNav === 'contacts' ? 'active' : ''}`} onClick={() => setSelectedNav('contacts')}>👥</button>
<button className={`nav-btn ${selectedNav === 'profile' ? 'active' : ''}`} onClick={() => setSelectedNav('profile')}>👤</button>
<button className={`nav-btn ${selectedNav === 'settings' ? 'active' : ''}`} onClick={() => setSelectedNav('settings')}>⚙️</button>

</div>

        <div className={`sidebar ${sidebarOpen ? '' : 'closed'}`}>
          <div className="contact-list">
{filteredContacts.map((c, i) => {
  const realIndex = contacts.findIndex(x => x.name === c.name);
  return (
    <div
      className={`contact ${selected === realIndex ? 'selected' : ''}`}
      key={realIndex}
      onClick={() => setSelected(realIndex)}
    >
      <div className="avatar-wrap">
        <img src={c.avatar} className="avatar-img" />
        <div className="dot" style={{ backgroundColor: c.online ? '#00FFAA' : '#777' }}></div>
      </div>
      <div>
        <div style={{ fontWeight: 'bold', color: '#fff' }}>{c.name}</div>
        <div style={{ fontSize: '12px', color: '#aaa' }}>{c.time}</div>
      </div>
    </div>
  );
})}

          </div>
        </div>

{selectedNav === 'contacts' && (
  <div className="main">
    <div className="chat-header">
  <div className="chat-avatar"></div>
  <div>
    <div style={{ fontWeight: 'bold' }}>{contacts[selected].name}</div>
    <div style={{ fontSize: '13px', color: '#aaa' }}>{contacts[selected].status}</div>
    <div style={{ fontSize: '12px', color: sharedKeys[contacts[selected].name] ? '#00FFAA' : '#f55' }}>
      {getKeyStatus()}
    </div>
  </div>
</div>


    <div className="pinned">
      📌 This is a pinned message.
    </div>

    <div className="messages">
{(searchTerm ? filteredMessages : messages).map((msg, i) => {
  const isMe = msg.sender === 'me';
  const isDelivered = msg.id && deliveredIds.includes(msg.id);

  return (
    <div key={i} className={`bubble ${isMe ? 'outgoing' : 'incoming'}`}>
      {msg.file ? (
  msg.type.startsWith('image/') ? (
    <img src={msg.url} alt={msg.name} style={{ maxWidth: '200px', borderRadius: '10px' }} />
  ) : msg.type.startsWith('audio/') ? (
    <audio controls style={{ width: '100%' }}>
      <source src={msg.url} type={msg.type} />
      Your browser does not support audio playback.
    </audio>
  ) : (
    <a href={msg.url} download={msg.name} style={{ color: '#00E5FF' }}>
      📄 {msg.name}
    </a>
  )
) : (
  <Decryptor text={msg.text} />
)}

      {isMe && (
        <span style={{ fontSize: '12px', marginLeft: '8px', color: isDelivered ? '#00FFAA' : '#888' }}>
          {isDelivered ? '✅✅' : '✅'}
        </span>
      )}
    </div>
  );
})}


      <div ref={messagesEndRef} />
    </div>

    <div className="input-bar">
      <button className="icon">😀</button>
      <label className="icon" style={{ cursor: 'pointer' }}>
  📎
  <input
  type="file"
  style={{ display: 'none' }}
  onChange={(e) => {
    const file = e.target.files[0];
    if (file) setPendingFile(file); // 🆕 store for preview
    handleFileUpload(e);
  }}
/>
</label>
{pendingFile && (
  <div style={{ color: '#ccc', fontSize: '13px', marginRight: '10px' }}>
    📎 {pendingFile.name} – {(pendingFile.size / 1024 / 1024).toFixed(2)} MB
  </div>
)}

      <input
        placeholder="Type a message..."
        value={input}
        onChange={(e) => setInput(e.target.value)}
        onKeyDown={(e) => {
          if (e.key === 'Enter') handleSend();
        }}
      />
      <button onClick={handleSend}>Send</button>
    </div>
  </div>
)}
{selectedNav === 'profile' && (
  <div className="main">
    <div className="chat-header">
      <div className="chat-avatar"></div>
      <div>
        <div style={{ fontWeight: 'bold' }}>My Profile</div>
        <div style={{ fontSize: '13px', color: '#aaa' }}>Status: Available</div>
      </div>
    </div>
    <div style={{ padding: '20px', color: '#ccc' }}>
      <p><strong>Username:</strong> {profile.name}</p>
      <p><strong>Bio:</strong> {profile.bio}</p>
      <p><strong>Status:</strong> Encrypted & Private 🛡️</p>
    </div>
  </div>
)}

{selectedNav === 'settings' && (
  <div className="main">
    <div className="chat-header">
      <div className="chat-avatar"></div>
      <div>
        <div style={{ fontWeight: 'bold' }}>Settings</div>
        <div style={{ fontSize: '13px', color: '#aaa' }}>App Preferences</div>
      </div>
    </div>
    <div style={{ padding: '20px', color: '#ccc' }}>
      <p><strong>Theme:</strong> Dark 🌑</p>
      <p><strong>Notifications:</strong> Enabled ✅</p>
      <p><strong>Storage:</strong> Local Only 🗂️</p>
    </div>
  </div>
)}
</div> {/* END of layout */}
{showDrawer && (
  <div className="drawer" onClick={() => setShowDrawer(false)}>
    <div className="drawer-sheet" onClick={(e) => e.stopPropagation()}>
      <div className="drawer-header">
        <span className="drawer-title">Menu</span>
        <button className="drawer-close" onClick={() => setShowDrawer(false)}>✖</button>
      </div>

      <div className="profile-section">
  <div className="avatar-container">
    <img className="profile-avatar" src="https://randomuser.me/api/portraits/men/75.jpg" />
  </div>
  <div className="profile-info">
    <div className="profile-name">{profile.name || 'Anonymous'}</div>
    <div className="online-status" style={{ color: '#00E5FF' }}>🟢 Online</div>
    <div className="last-seen">Last seen: 2 min ago</div>
  </div>
  <div className="bio-box">
    <div className="bio-label">Bio</div>
    <div className="bio-text">{profile.bio || 'No bio set.'}</div>
  </div>
</div>


      <div className="drawer-section">
        <button className="drawer-btn">✏️ Edit Profile</button>
        <button className="drawer-btn">🔑 Change Password</button>
        <button className="drawer-btn">📜 Update Bio</button>
        <button
          className="drawer-btn"
          onClick={() => {
            localStorage.removeItem('siphrix_session');
            router.push('/login');
          }}
        >
          🚪 Logout
        </button>
        <button className="drawer-btn danger" onClick={panicWipe}>🧨 Panic Delete</button>
      </div>
    </div>
  </div>
)}

</>
);
}