import { useState } from "react";
import "./chatbot.css";
import logoUdem from "../public/logo_udemedellin2.png";
import { Link } from "react-router-dom";

function Chatbot() {
  const [messages, setMessages] = useState([
    {
      text: "🎓 ¡Hola! Soy PromeIA, el asistente virtual de la Universidad de Medellín.",
      type: "bot",
    },
    {
      text: "Puedo orientarte sobre materias, profesores, eventos y servicios universitarios. Para preguntas generales puedes empezar sin identificarte.",
      type: "bot",
    },
  ]);
  const [inputValue, setInputValue] = useState("");
  const [identificacion, setIdentificacion] = useState(null);
  const [nombreUsuario, setNombreUsuario] = useState(null);
  const [esperandoIdentificacion, setEsperandoIdentificacion] = useState(true);
  const [cargandoIA, setCargandoIA] = useState(false);

  const mostrarMensaje = (texto, tipo) => {
    const urlRegex = /(https?:\/\/[^\s]+)/g;
    const textoConLinks = texto.replace(
      urlRegex,
      '<a href="$1" target="_blank">haz clic aquí</a>'
    );
    setMessages((prev) => [...prev, { text: textoConLinks, type: tipo }]);
  };

  const verificarIdentificacion = async (id) => {
    try {
      const response = await fetch(
        `/api/ai/verificar_identificacion/${encodeURIComponent(id)}`
      );
      const data = await response.json();
      return data;
    } catch (error) {
      console.error("Error verificando identificación:", error);
      return { encontrado: false };
    }
  };

  const consultarIA = async (pregunta) => {
    setCargandoIA(true);
    try {
      const response = await fetch("/api/ai/generate", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          prompt: pregunta,
          max_tokens: 800,
          temperature: 0.7,
          identificacion: identificacion, // Enviar la identificación si existe
          usar_contexto: true, // Siempre usar contexto
        }),
      });

      const data = await response.json();

      // Si hay error HTTP, mostrar detalle
      if (!response.ok) {
        console.error("Error de respuesta:", data);
        const errorMsg = data.detail
          ? typeof data.detail === "string"
            ? data.detail
            : JSON.stringify(data.detail)
          : `Error ${response.status}: ${response.statusText}`;
        mostrarMensaje(`❌ Error: ${errorMsg}`, "bot");
        return;
      }

      if (data.identificacion_validada === false) {
        mostrarMensaje(
          "⚠️ No pude validar esa identificación. Responderé sin usar información académica personal; puedes continuar con preguntas generales.",
          "bot"
        );
      }

      if (data.text) {
        mostrarMensaje(`🤖 ${data.text}`, "bot");
      } else if (data.detail) {
        mostrarMensaje(`❌ Error: ${data.detail}`, "bot");
      }
    } catch (error) {
      console.error("Error al consultar la IA:", error);
      mostrarMensaje(`❌ Error al consultar la IA: ${error.message}`, "bot");
    } finally {
      setCargandoIA(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!inputValue.trim()) return;

    mostrarMensaje(inputValue, "user");

    // Si está esperando identificación
    if (esperandoIdentificacion) {
      const entrada = inputValue.trim();
      const quiereOmitirId = /^(omitir|continuar|sin identificaci[oó]n)$/i.test(entrada);
      const pareceIdentificacion = /^\d{5,15}$/.test(entrada);

      if (quiereOmitirId) {
        mostrarMensaje(
          "✅ Continuemos sin identificación. ¿En qué puedo ayudarte?",
          "bot"
        );
        setEsperandoIdentificacion(false);
      } else if (pareceIdentificacion) {
        const id = entrada;
        // Verificar identificación en la base de datos
        mostrarMensaje("🔍 Verificando identificación...", "bot");
        const resultado = await verificarIdentificacion(id);

        if (resultado.encontrado) {
          // Guardar identificación y nombre
          setIdentificacion(id);
          setNombreUsuario(resultado.nombre);
          mostrarMensaje(
            `✅ ¡Bienvenid@ ${resultado.nombre}! 👋\n\nTipo de usuario: ${resultado.tipo}\n\nAhora puedo darte información personalizada. ¿En qué puedo ayudarte?`,
            "bot"
          );
        } else {
          mostrarMensaje(
            `⚠️ No encontré la identificación "${id}" en el sistema.\n\nPuedes continuar sin identificación o intentar con otro número. ¿En qué puedo ayudarte?`,
            "bot"
          );
        }
        setEsperandoIdentificacion(false);
      } else {
        // Una entrada que no parece un documento se trata como la primera pregunta.
        setEsperandoIdentificacion(false);
        consultarIA(entrada);
      }
      setInputValue("");
      return;
    }

    // Consultar IA
    consultarIA(inputValue);
    setInputValue("");
  };

  return (
    <div className="chatbot-page">
      <header className="chat-header">
        <Link className="chat-back-link" to="/" aria-label="Volver al inicio">
          <span className="chat-back-arrow" aria-hidden="true">←</span>
          <span>Volver</span>
        </Link>

        <div className="chat-identity">
          <img src={logoUdem} alt="Universidad de Medellín" />
          <div className="chat-identity-copy">
            <strong>PromeIA</strong>
            <span>Universidad de Medellín</span>
          </div>
        </div>

        <div className="chat-header-right">
          <div className="chat-presence" aria-label="Asistente disponible">
            <span className="chat-presence-dot" aria-hidden="true" />
            <span>Disponible</span>
          </div>
          {nombreUsuario && <div className="user-badge">👤 {nombreUsuario}</div>}
        </div>
      </header>

      <main className="chat-main">
        <div className="chat-intro">
          <p className="eyebrow">Asistente virtual</p>
          <h1>¿En qué puedo ayudarte?</h1>
          <p>Escribe tu pregunta con tus propias palabras. Estoy aquí para orientarte.</p>
        </div>

        <section className="chat-panel" aria-label="Conversación con PromeIA">
          <div className="chat-box" role="log" aria-live="polite" aria-relevant="additions">
            {messages.map((msg, index) => (
              <div
                key={index}
                className={`${msg.type}-message`}
                dangerouslySetInnerHTML={{ __html: msg.text }}
              />
            ))}
            {cargandoIA && (
              <div className="chat-thinking" role="status">
                <span>PromeIA está preparando una respuesta</span>
                <span className="thinking-dots" aria-hidden="true">
                  <span />
                  <span />
                  <span />
                </span>
              </div>
            )}
          </div>

          <div className="input-container">
            <form onSubmit={handleSubmit}>
              <input
                className="message-input"
                type="text"
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                placeholder={
                  esperandoIdentificacion
                    ? "Escribe una pregunta o tu identificación (opcional)"
                    : "Escribe tu pregunta..."
                }
                aria-label="Escribe tu mensaje para PromeIA"
                disabled={cargandoIA}
              />
              <button
                className="send-button"
                type="submit"
                aria-label="Enviar mensaje"
                disabled={cargandoIA}
              >
                <span aria-hidden="true">➤</span>
              </button>
              <button
                className="reset-button"
                onClick={() => window.location.reload()}
                type="button"
                aria-label="Iniciar una nueva conversación"
                title="Nueva conversación"
              >
                <span aria-hidden="true">↻</span>
              </button>
            </form>
            <p className="input-hint">
              La identificación es opcional para consultas generales. No compartas contraseñas ni datos sensibles.
            </p>
          </div>
        </section>
      </main>
    </div>
  );
}

export default Chatbot;
