// utils/peer_connection.js

let peer = null;
let dataChannel = null;
let onMessageCallback = null;

export async function initConnection(onMessage) {
  peer = new RTCPeerConnection({
    iceServers: [{ urls: "stun:stun.l.google.com:19302" }],
  });

  dataChannel = peer.createDataChannel("chat");
  onMessageCallback = onMessage;

  dataChannel.onmessage = (event) => {
    if (onMessageCallback) onMessageCallback(event.data);
  };

  await new Promise((resolve) => {
    peer.onicecandidate = (e) => {
      if (!e.candidate) resolve();
    };
  });

  const offer = await peer.createOffer();
  await peer.setLocalDescription(offer);

  return JSON.stringify(peer.localDescription);
}

export async function connectToOffer(offerSDP, onMessage) {
  peer = new RTCPeerConnection({
    iceServers: [{ urls: "stun:stun.l.google.com:19302" }],
  });

  onMessageCallback = onMessage;

  peer.ondatachannel = (event) => {
    dataChannel = event.channel;
    dataChannel.onmessage = (e) => {
      if (onMessageCallback) onMessageCallback(e.data);
    };
  };

  await peer.setRemoteDescription(JSON.parse(offerSDP));
  const answer = await peer.createAnswer();
  await peer.setLocalDescription(answer);

  await new Promise((resolve) => {
    peer.onicecandidate = (e) => {
      if (!e.candidate) resolve();
    };
  });

  return JSON.stringify(peer.localDescription);
}

export function completeConnection(answerSDP) {
  return peer.setRemoteDescription(JSON.parse(answerSDP));
}

export function sendMessage(message) {
  if (dataChannel && dataChannel.readyState === "open") {
    dataChannel.send(message);
  } else {
    console.warn("❌ DataChannel not open");
  }
}
