// src/components/InputArea.jsx
import { useState } from 'react';

export default function InputArea({ onSend, disabled }) {
  const [input, setInput] = useState('');

  const handleSubmit = (e) => {
    e.preventDefault();
    if (input.trim() && !disabled) {
      onSend(input);
      setInput('');
    }
  };

  return (
    <form className="input-area" onSubmit={handleSubmit}>
      <input
        type="text"
        value={input}
        onChange={(e) => setInput(e.target.value)}
        placeholder="Escribe tu pregunta sobre pensión de alimentos..."
        disabled={disabled}
      />
      <button type="submit" disabled={disabled}>Enviar</button>
    </form>
  );
}