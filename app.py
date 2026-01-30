CHAT_HTML = """
<!doctype html>
<html>
<head>
  <title>Chat Bot</title>
  <style>
    body {
      font-family: Arial, sans-serif;
      background: #ece5dd;
    }
    .chat {
      max-width: 600px;
      margin: 30px auto;
      background: #fff;
      padding: 15px;
      border-radius: 10px;
      box-shadow: 0 0 10px rgba(0,0,0,0.1);
    }
    .msg {
      margin: 10px 0;
      max-width: 80%;
      padding: 10px 14px;
      border-radius: 10px;
      white-space: pre-line;
    }
    .user-msg {
      background: #dcf8c6;
      margin-left: auto;
      text-align: right;
    }
    .bot-msg {
      background: #f1f0f0;
      margin-right: auto;
    }
    .sender {
      font-size: 12px;
      opacity: 0.6;
      margin-bottom: 4px;
    }
    form {
      display: flex;
      gap: 8px;
      margin-top: 15px;
    }
    input {
      flex: 1;
      padding: 10px;
      border-radius: 6px;
      border: 1px solid #ccc;
    }
    button {
      padding: 10px 14px;
      border-radius: 6px;
      border: none;
      background: #128c7e;
      color: white;
      cursor: pointer;
    }
    .clear {
      text-align: center;
      margin-top: 10px;
    }
    .clear a {
      font-size: 12px;
      color: #888;
      text-decoration: none;
    }
  </style>
</head>
<body>
  <div class="chat">
    {% for m in messages %}
      <div class="msg {% if m.sender == 'Tú' %}user-msg{% else %}bot-msg{% endif %}">
        <div class="sender">{{ m.sender }}</div>
        {{ m.text }}
      </div>
    {% endfor %}

    <form method="post">
      <input name="message" placeholder="Escribe un mensaje..." autofocus required>
      <button>Enviar</button>
    </form>

    <div class="clear">
      <a href="/clear">🗑 Borrar conversación</a>
    </div>
  </div>
</body>
</html>
"""
