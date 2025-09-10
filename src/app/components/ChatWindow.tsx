import { useState } from "react";
import {
  Button,
  InputBase,
  IconButton,
  Box,
  Typography,
  Paper,
} from "@mui/material";
import SmartToyIcon from "@mui/icons-material/SmartToy";
import SendIcon from "@mui/icons-material/Send";
import AccountCircleIcon from "@mui/icons-material/AccountCircle";
import { useTheme } from "@mui/material/styles";

interface ChatMessage {
  id: string;
  content: string;
  sender: "user" | "ai";
  timestamp: Date;
}

interface ChatWindowProps {
  isOpen: boolean;
  onClose: () => void;
}

export default function ChatWindow({ isOpen, onClose }: ChatWindowProps) {
  const theme = useTheme();
  const [loading, setLoading] = useState(false)
  const [response, setResponse] = useState<string>("");

  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: "1",
      content:
        "Hello! I can help you create and validate data quality rules. Select a column and describe what you want to validate.",
      sender: "ai",
      timestamp: new Date(),
    },
]);
const [inputValue, setInputValue] = useState("");


const handleSendMessage = () => {
  const trimmed = inputValue.trim();
  if (!trimmed) return;

  // Add user message
  const userMessage: ChatMessage = {
    id: String(Date.now()),
    content: trimmed,
    sender: "user",
    timestamp: new Date(),
  };

  const updatedMessages = [...messages, userMessage];
  setMessages(updatedMessages);
  setInputValue("");

  askAI(updatedMessages);
};

const askAI = async (conversation: ChatMessage[]) => {
  setLoading(true);

  try {
    // Map ChatMessage to the format expected by GPT
    const messagesForAPI = [
      {
        role: "system",
        content: `You are an expert assistant specialized in generating concise SQL validation rules.
Produce output strictly in the following format:
Rule: <Your most relevant SQL validation rule query here>
Explanation: <Brief reason why this rule is appropriate in this context>
Do not add any additional text or commentary beyond this format.`,
      },
      ...conversation.map((msg) => ({
        role: msg.sender === "user" ? "user" : "assistant",
        content: msg.content,
      })),
    ];

    const API_BASE_URL =
      process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

    const res = await fetch(`${API_BASE_URL}/api/groq-chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ messages: messagesForAPI }),
    });

    if (!res.ok) throw new Error("API request failed");

    const data = await res.json();

    // Add AI response message
    const aiMessage: ChatMessage = {
      id: String(Date.now() + 1),
      content: data.response,
      sender: "ai",
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, aiMessage]);
  } catch (e) {
    const errorMessage: ChatMessage = {
      id: String(Date.now() + 2),
      content: "Error fetching AI response.",
      sender: "ai",
      timestamp: new Date(),
    };
    setMessages((prev) => [...prev, errorMessage]);
  } finally {
    setLoading(false);
  }
};

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === "Enter") {
      handleSendMessage();
    }
  };

  if (!isOpen) return null;

  return (
    <Box
      sx={{
        position: "fixed",
        top: 0,
        right: 0,
        height: "100vh",
        width: 400,
        bgcolor: theme.palette.background.paper,
        zIndex: 40,
        boxShadow: 8,
        borderLeft: `1px solid ${theme.palette.divider}`,
        display: "flex",
        flexDirection: "column",
      }}
    >
      {/* Chat Header */}
      <Box
        sx={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          p: 2,
          borderBottom: `1px solid ${theme.palette.divider}`,
        }}
      >
        <Box sx={{ display: "flex", alignItems: "center", gap: 2 }}>
          <Box
            sx={{
              width: 32,
              height: 32,
              bgcolor: theme.palette.primary.main,
              borderRadius: "50%",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
            }}
          >
            <SmartToyIcon
              sx={{ color: theme.palette.primary.contrastText, fontSize: 20 }}
            />
          </Box>
          <Box>
            <Typography
              variant="subtitle1"
              fontWeight="bold"
              color="text.primary"
            >
              AI Assistant
            </Typography>
            <Typography variant="caption" color="text.secondary">
              Ready to help with rules
            </Typography>
          </Box>
        </Box>

      </Box>

      {/* Chat Messages */}
      <Box
        sx={{
          flex: 1,
          overflowY: "auto",
          p: 2,
          bgcolor: theme.palette.background.default,
        }}
      >
        {messages.map((message) => (
          <Box
            key={message.id}
            sx={{
              display: "flex",
              alignItems: "flex-end",
              justifyContent:
                message.sender === "user" ? "flex-end" : "flex-start",
              gap: 1,
              mb: 2,
            }}
          >
            {message.sender === "ai" && (
              <Box
                sx={{
                  width: 28,
                  height: 28,
                  bgcolor: theme.palette.primary.main,
                  borderRadius: "50%",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  flexShrink: 0,
                }}
              >
                <SmartToyIcon
                  sx={{
                    color: theme.palette.primary.contrastText,
                    fontSize: 18,
                  }}
                />
              </Box>
            )}
            <Paper
              elevation={1}
              sx={{
                p: 1.5,
                px: 2,
                maxWidth: 250,
                bgcolor:
                  message.sender === "ai"
                    ? theme.palette.grey[100]
                    : theme.palette.primary.main,
                color:
                  message.sender === "ai"
                    ? theme.palette.text.primary
                    : theme.palette.primary.contrastText,
                borderRadius: 2,
                fontSize: 14,
              }}
            >
              {message.content}
            </Paper>
            {message.sender === "user" && (
              <Box
                sx={{
                  width: 28,
                  height: 28,
                  bgcolor: theme.palette.secondary.main,
                  borderRadius: "50%",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  flexShrink: 0,
                }}
              >
                <AccountCircleIcon
                  sx={{
                    color: theme.palette.secondary.contrastText,
                    fontSize: 18,
                  }}
                />
              </Box>
            )}
          </Box>
        ))}
      </Box>

      {/* Chat Input */}
      <Box
        sx={{
          borderTop: `1px solid ${theme.palette.divider}`,
          p: 2,
        }}
      >
        <Box sx={{ display: "flex", gap: 1 }}>
          <InputBase
            fullWidth
            placeholder="Ask about data rules..."
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyUp={handleKeyPress}
            sx={{
              bgcolor: theme.palette.grey[100],
              px: 2,
              py: 1,
              borderRadius: 2,
              fontSize: 16,
            }}
          />
          <IconButton
            color="primary"
            onClick={handleSendMessage}
            disabled={!inputValue.trim()}
            sx={{ px: 2, borderRadius: 2 }}
          >
            <SendIcon />
          </IconButton>
        </Box>
      </Box>
    </Box>
  );
}
