import React, { useState } from "react";
import { Button, OverlayTrigger, Tooltip } from "react-bootstrap";
import { ReactComponent as Copy } from "src/components/CopyToClipboardButton/copy.svg";

interface Props {
  text: string;
}

const CopyToClipboardButton = ({ text }: Props) => {
  const [isClicked, setIsClicked] = useState(false);
  const [message, setMessage] = useState("");

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(text);
      setIsClicked(true);
      setMessage("Copied to clipboard!");
      setTimeout(() => {
        setIsClicked(false);
      }, 3000);
    } catch (error) {
      setIsClicked(true);
      setMessage("Failed to copy slug");
      setTimeout(() => {
        setIsClicked(false);
      }, 3000);
      console.error(error);
    }
  };

  return (
    <OverlayTrigger
      placement="top"
      overlay={<Tooltip id="tooltip-copy">{message}</Tooltip>}
      show={isClicked}
    >
      <Button
        data-testid="copy-button"
        variant="outlined"
        className="rounded-circle border-0 mb-2 shadow-none pt-0 pr-0 pb-0 pl-1"
        onClick={handleCopy}
      >
        <Copy
          data-testid="copy-to-clipboard-icon"
          onMouseOver={(e) => (e.currentTarget.style.transform = "scale(1.2)")}
          onMouseOut={(e) => (e.currentTarget.style.transform = "scale(1)")}
          width="18"
          height="18"
          title="Copy to Clipboard"
        />
      </Button>
    </OverlayTrigger>
  );
};

export default CopyToClipboardButton;
