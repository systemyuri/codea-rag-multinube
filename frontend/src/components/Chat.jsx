// src/components/Chat.jsx
import { useState } from 'react';
import Message from './Message';
import InputArea from './InputArea';
import { sendQuestion } from '../services/api';
import './Chat.css';

export default function Chat() {
  const [messages, setMessages] = useState([
    { text: "Hola, soy el asistente 'Alimentos al Día'. Puedo orientarte sobre requisitos y procedimientos para la pensión de alimentos en Perú. Recuerda que esto no es asesoría legal vinculante.", isUser: false }
  ]);
  const [loading, setLoading] = useState(false);

  const handleSend = async (question) => {
    setMessages(prev => [...prev, { text: question, isUser: true }]);
    setLoading(true);
    try {
      const answer = await sendQuestion(question);
      setMessages(prev => [...prev, { text: answer, isUser: false }]);
    } catch (error) {
      setMessages(prev => [...prev, { text: "Lo siento, ocurrió un error. Intenta de nuevo más tarde.", isUser: false }]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="chat-container">
      <div className="messages">
        {messages.map((msg, idx) => (
          <Message key={idx} text={msg.text} isUser={msg.isUser} />
        ))}
        {loading && <div className="typing">El asistente está escribiendo...</div>}
      </div>
      <InputArea onSend={handleSend} disabled={loading} />
    </div>
  );
}