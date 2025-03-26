import React from "react";
import { Streamlit, withStreamlitConnection } from "streamlit-component-lib";

interface Props {
  args: {
    name: string;
  };
  width: number;
  disabled: boolean;
}

const MyComponent = ({ args }: Props) => {
  const { name } = args;

  return (
    <div style={{ padding: "1rem", backgroundColor: "#f5f5f5", borderRadius: "8px" }}>
      <h3>👋 안녕하세요, {name} 님!</h3>
      <p>Streamlit 커스텀 컴포넌트로부터 데이터를 받았습니다.</p>
    </div>
  );
};

export default withStreamlitConnection(MyComponent);
