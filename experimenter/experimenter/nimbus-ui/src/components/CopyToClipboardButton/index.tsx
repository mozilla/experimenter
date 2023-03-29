import React, { useState } from "react";
import { Button, OverlayTrigger, Tooltip } from "react-bootstrap";
import { ReactComponent as Copy } from "src/components/CopyToClipboardButton/copy.svg";

interface Props {
  text: string;
}

const CopyToClipboardButton = ({ text }: Props) => {
  const [isCopied, setIsCopied] = useState(false);

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(text);
      setIsCopied(true);
      setTimeout(() => {
        setIsCopied(false);
      }, 3000);
    } catch (error) {
      console.error(error);
    }
  };

  return (
    <OverlayTrigger
      placement="top"
      overlay={<Tooltip id="tooltip-copy">{isCopied && "Copied!"}</Tooltip>}
      show={isCopied}
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
