import "./App.css";
import logoUdem from "../public/logo_udemedellin2.png";
import { Link } from "react-router-dom";

const cursos = [
  "Fundamentos de Diseño de Software",
  "Cálculo",
  "Legislación",
  "Física II",
];

export default function Index() {
  return (
    <div className="portal-page">
      <header className="portal-header">
        <Link to="/" className="portal-brand" aria-label="Campus virtual Universidad de Medellín">
          <img src={logoUdem} alt="Universidad de Medellín" />
          <span className="portal-brand-divider" aria-hidden="true" />
          <span>
            Campus virtual
            <span className="portal-brand-caption">Universidad de Medellín</span>
          </span>
        </Link>

        <nav className="portal-nav" aria-label="Navegación principal">
          <Link className="portal-nav-link active" to="/">Inicio</Link>
          <a className="portal-nav-link" href="#cursos">Mis cursos</a>
          <Link className="portal-nav-cta" to="/chatbot">
            Asistente virtual <span aria-hidden="true">↗</span>
          </Link>
        </nav>
      </header>

      <main className="portal-main">
        <section className="portal-hero" aria-labelledby="portal-title">
          <div className="hero-copy">
            <p className="eyebrow">Universidad de Medellín · Campus virtual</p>
            <h1 id="portal-title">Tu vida académica, en un solo lugar</h1>
            <p className="hero-description">
              Explora tus espacios de aprendizaje y encuentra acompañamiento para
              resolver tus inquietudes universitarias.
            </p>
            <div className="hero-actions">
              <Link className="primary-link" to="/chatbot">
                Hablar con PromeIA <span aria-hidden="true">→</span>
              </Link>
              <a className="secondary-link" href="#cursos">Explorar mis cursos</a>
            </div>
          </div>

          <aside className="hero-assistant-card" aria-label="Información sobre PromeIA">
            <div className="assistant-card-icon" aria-hidden="true">✦</div>
            <p className="assistant-card-label">Acompañamiento digital</p>
            <h2>Conoce a PromeIA</h2>
            <p>Una guía virtual para orientarte en tu experiencia universitaria.</p>
          </aside>
        </section>

        <section className="courses-section" id="cursos" aria-labelledby="courses-title">
          <div className="section-heading">
            <div>
              <p className="section-eyebrow">Aprendizaje</p>
              <h2 id="courses-title">Tus espacios académicos</h2>
            </div>
            <p>Accesos a los cursos que aparecen en tu campus.</p>
          </div>

          <div className="course-grid">
            {cursos.map((curso) => (
              <article className="course-card" key={curso}>
                <span className="course-card-label">Espacio académico</span>
                <h3>{curso}</h3>
              </article>
            ))}
          </div>
        </section>

        <section className="support-banner" aria-labelledby="support-title">
          <div>
            <h2 id="support-title">¿Tienes una pregunta?</h2>
            <p>PromeIA puede orientarte sobre materias, profesores, eventos y servicios universitarios.</p>
          </div>
          <Link className="secondary-link" to="/chatbot">
            Abrir el asistente <span aria-hidden="true">→</span>
          </Link>
        </section>
      </main>

      <Link to="/chatbot" className="chatbot-btn" aria-label="Abrir asistente virtual" title="Abrir PromeIA">
        <span aria-hidden="true">💬</span>
      </Link>
    </div>
  );
}
