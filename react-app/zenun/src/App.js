import React from 'react';
import './App.css';
import RegisterPage from './pages/RegisterPage'; // Importa el componente de la página de registro

function App() {
  return (
    <div className="App">
      <header className="App-header">
        <RegisterPage /> {/* Usa el componente de la página de registro aquí */}
      </header>
    </div>
  );
}

export default App;
