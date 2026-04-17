import { useEffect, useState } from "react";
import "./App.css";

// For easy access and a one stop place to change port number
const API_URL = import.meta.env.VITE_API_URL;

function App() {
  const [letters, setLetters] = useState([]);
  const [centerLetter, setCenterLetter] = useState("");
  const [wordInput, setWordInput] = useState("");
  const [foundWords, setFoundWords] = useState([]);
  const [score, setScore] = useState(0);
  const [rank, setRank] = useState("Beginner");
  const [message, setMessage] = useState("");

  // 1. Attempt to get 'session_id' from the browser's temporary storage.
  // 2. The '||' (OR operator) acts as a fallback: 
  //    if the ID doesn't exist (null), it generates a new unique string using crypto.randomUUID().
  const sessionId = sessionStorage.getItem("session_id") || crypto.randomUUID();

  // 3. Save the ID (either the retrieved one or the new one) back into storage.
  //    This ensures the same ID is found the next time the page is refreshed.
  sessionStorage.setItem("session_id", sessionId);

  // Fetch letters
  useEffect(() => {
    fetch(`${API_URL}/api/game/today`)
      .then(res => res.json())
      .then(data => {
        setCenterLetter(data.data.center);
        setLetters(data.data.letters);
      });
  }, []);

  // Fetch found words
  useEffect(() => {
    fetch(`${API_URL}/api/found_words?session_id=${sessionId}`)
      .then(res => res.json())
      .then(data => {
        const d = data.data;
        setFoundWords(d.found_words);
        setScore(d.total_points);
        setRank(d.rank);
      });
  }, []);

  // clean functional update, garanties most uptodate state info
  const handleLetterClick = (letter) => {
    setWordInput(prev => prev + letter);
  };

  const submitWord = () => {
    const word = wordInput.trim();
    if (!word) return;

    fetch(`${API_URL}/api/check_word`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({ word, session_id: sessionId })
    })
      .then(res => res.json())
      .then(data => {
        if (data.status === "fail") {
          setMessage(data.reason);
        } else if (data.status === "error") {
          setMessage(data.message);
        } else if (data.status === "ok") {
          const d = data.data;

          setScore(d.total_points);
          setRank(d.rank);
          setFoundWords(prev => [...prev, word]);

          if (d.pangram) {
            setMessage("Pangram!! Bonus Points!");
          } else {
            setMessage("");
          }
        }

        setWordInput("");
      });
  };

  const restartGame = () => {
    fetch(`${API_URL}/api/restart`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({ session_id: sessionId })
    })
      .then(res => res.json())
      .then(data => {
        if (data.status === "ok") {
          setFoundWords([]);
          setScore(0);
          setRank("Beginner");
          setMessage("");
          setWordInput("");
        }
      });
  };

  const safeLetters = letters || [];

  const orderedLetters = [
    ...safeLetters.filter(l => l !== centerLetter)
  ]; const midIndex = Math.floor(orderedLetters.length / 2);
  orderedLetters.splice(midIndex, 0, centerLetter);

  // back space button
  const handleBackspace = () => {
    setWordInput(prev => prev.slice(0, -1));
  };
  return (
    <div className="containerOuter">
      <div className="containerInner">
        <h1>Spelling Bee</h1>

        <div className="letters">
          {!letters.length || !centerLetter ? (
            <div className="spinner"></div>
          ) : (
            orderedLetters.map((l, i) => (
              <span
                key={i}
                className={`letter ${l === centerLetter ? "center" : ""}`}
                onClick={() => handleLetterClick(l)}
              >
                {l.toUpperCase()}
              </span>
            ))
          )}
        </div>
        <div id="inputArea">
          <input
            className="textInput"
            type="text"
            value={wordInput}
            placeholder="Type your word here..."
            onChange={(e) => setWordInput(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter") submitWord();
              if (e.key === "Backspace") handleBackspace();
            }}
            autoFocus
          />
        </div>
        <div id="inputArea">
          <button onClick={handleBackspace}>Back-Space</button>
          <button onClick={submitWord}>Submit</button>
          <button onClick={restartGame}>Restart</button>
        </div>

        <div className="message">{message}</div>

        <div className="scoreboard">
          <h2>Score: {score}</h2>
          <h2>Rank: {rank}</h2>
        </div>

        <div>
          <h3>Found Words:</h3>
          <ul>
            {foundWords.map((word, i) => (
              <li key={i}>{word.toUpperCase()}</li>
            ))}
          </ul>
        </div>
      </div>
    </div>
  );
}

export default App;