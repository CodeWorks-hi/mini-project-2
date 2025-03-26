// src/App.tsx
import React from "react";
import MyComponent from "./MyComponent";

function App() {
  return (
    <div style={{ padding: "2rem" }}>
      <h1>🎯 React 커스텀 컴포넌트 테스트</h1>
      <MyComponent name="홍길동" />
    </div>
  );
}

export default App;
