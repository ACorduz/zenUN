import React, { useState } from 'react';
import './RegisterPage.css';

const RegisterPage = () => {
  const [formData, setFormData] = useState({
    fullName: '',
    email: '',
    password: '',
    confirmPassword: '',
    documentType: '',
    documentNumber: '',
  });

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData({
      ...formData,
      [name]: value,
    });
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    console.log('Formulario enviado:', formData);
  };

  return (
    <div className="register-page-container">
      <div className="form-container">
        <div className="form-title-container">
          <div className="logo"></div>
          <h2 className="form-title">Crea tu cuenta</h2>
        </div>
        <div className="form-content">
          <div className="form-group">
            <label htmlFor="fullName">Nombre completo:</label>
            <input
              type="text"
              id="fullName"
              name="fullName"
              value={formData.fullName}
              onChange={handleChange}
              required
            />
          </div>
          <div className="form-group">
            <label htmlFor="email">Correo:</label>
            <input
              type="email"
              id="email"
              name="email"
              value={formData.email}
              onChange={handleChange}
              required
            />
          </div>
          <div className="form-group">
            <label htmlFor="password">Contraseña:</label>
            <input
              type="password"
              id="password"
              name="password"
              value={formData.password}
              onChange={handleChange}
              required
            />
          </div>
          <div className="form-group">
            <label htmlFor="confirmPassword">Verificación de contraseña:</label>
            <input
              type="password"
              id="confirmPassword"
              name="confirmPassword"
              value={formData.confirmPassword}
              onChange={handleChange}
              required
            />
          </div>
          <div className="form-group">
            <label htmlFor="documentType">Tipo de documento:</label>
            <input
              type="text"
              id="documentType"
              name="documentType"
              value={formData.documentType}
              onChange={handleChange}
              required
            />
          </div>
          <div className="form-group">
            <label htmlFor="documentNumber">Número de documento:</label>
            <input
              type="text"
              id="documentNumber"
              name="documentNumber"
              value={formData.documentNumber}
              onChange={handleChange}
              required
            />
          </div>
          <button type="submit">Registrarse</button>
        </div>
      </div>
      <div className="image-container"></div>
    </div>
  );
};

export default RegisterPage;
