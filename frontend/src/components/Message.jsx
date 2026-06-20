export default function Message({ text, isUser }) {
  return (
    <div className={`message ${isUser ? 'user' : 'bot'}`}>
      <div className="avatar">{isUser ? '👤' : '⚖️'}</div>
      <div className="bubble">{text}</div>
    </div>
  );
}