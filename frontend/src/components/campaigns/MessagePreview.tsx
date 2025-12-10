"use client";

import { useMemo } from "react";

interface MessagePreviewProps {
  /** Contenu du message */
  content: string;
  /** Type de message */
  type?: "message_1" | "message_2";
  /** Afficher l'heure */
  showTime?: boolean;
}

/**
 * Prévisualisation d'un message style WhatsApp
 */
export function MessagePreview({
  content,
  type = "message_1",
  showTime = true,
}: MessagePreviewProps) {
  // Formater le contenu avec les liens cliquables
  const formattedContent = useMemo(() => {
    if (!content) return null;

    // Regex pour détecter les URLs
    const urlRegex = /(https?:\/\/[^\s]+)/g;
    const parts = content.split(urlRegex);

    return parts.map((part, index) => {
      if (urlRegex.test(part)) {
        return (
          <a
            key={index}
            href={part}
            target="_blank"
            rel="noopener noreferrer"
            className="text-blue-400 underline break-all"
          >
            {part}
          </a>
        );
      }
      // Préserver les sauts de ligne
      return part.split("\n").map((line, lineIndex) => (
        <span key={`${index}-${lineIndex}`}>
          {lineIndex > 0 && <br />}
          {line}
        </span>
      ));
    });
  }, [content]);

  const currentTime = new Date().toLocaleTimeString("fr-FR", {
    hour: "2-digit",
    minute: "2-digit",
  });

  if (!content) {
    return (
      <div className="bg-gray-900 rounded-lg p-4 min-h-[200px] flex items-center justify-center">
        <p className="text-gray-500 text-sm">
          Saisissez un message pour voir la prévisualisation
        </p>
      </div>
    );
  }


  return (
    <div className="bg-gray-900 rounded-lg p-4 min-h-[200px]">
      {/* Header WhatsApp style */}
      <div className="flex items-center gap-3 mb-4 pb-3 border-b border-gray-700">
        <div className="w-10 h-10 rounded-full bg-green-600 flex items-center justify-center text-white font-semibold">
          W
        </div>
        <div>
          <p className="text-white font-medium">WhatsApp Business</p>
          <p className="text-gray-400 text-xs">Prévisualisation</p>
        </div>
      </div>

      {/* Message bubble */}
      <div className="flex justify-end">
        <div className="max-w-[85%] bg-green-700 rounded-lg rounded-tr-none p-3 shadow-md">
          {/* Badge type de message */}
          <div className="mb-1">
            <span className="text-xs bg-green-800 text-green-200 px-2 py-0.5 rounded">
              {type === "message_1" ? "Message 1 (Template)" : "Message 2 (Suivi)"}
            </span>
          </div>
          
          {/* Contenu du message */}
          <p className="text-white text-sm whitespace-pre-wrap break-words">
            {formattedContent}
          </p>
          
          {/* Heure et statut */}
          {showTime && (
            <div className="flex items-center justify-end gap-1 mt-1">
              <span className="text-xs text-green-200">{currentTime}</span>
              <svg
                className="w-4 h-4 text-blue-400"
                fill="currentColor"
                viewBox="0 0 24 24"
              >
                <path d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41L9 16.17z" />
              </svg>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default MessagePreview;
