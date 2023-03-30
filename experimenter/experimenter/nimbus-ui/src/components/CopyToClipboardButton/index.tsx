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
        className="rounded-circle copy-button"
        onClick={handleCopy}
      >
        <Copy className="copy-to-clipboard-icon" title="" />
      </Button>
    </OverlayTrigger>
  );
};

export default CopyToClipboardButton;
