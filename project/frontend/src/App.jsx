import { useState, useEffect } from "react";
import {
  BrowserRouter as Router,
  Routes,
  Route,
  useNavigate,
} from "react-router-dom";
import "./App.css";

const API_BASE = import.meta.env.VITE_API_BASE || "http://localhost:5000/api";

const Home = () => {
  const [player, setPlayer] = useState({ health: 100, damage: 10, level: 1 });
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    fetchPlayerStats();
  }, []);

  const fetchPlayerStats = async () => {
    try {
      const response = await fetch(`${API_BASE}/player`);
      const data = await response.json();
      setPlayer(data);
      setLoading(false);
    } catch (error) {
      console.error("Error fetching player stats:", error);
      setLoading(false);
    }
  };

  const handleDungeonClick = () => {
    navigate("/dungeon");
  };

  if (loading) {
    return (
      <div className="game-container">
        <h1>Loading...</h1>
      </div>
    );
  }

  return (
    <div className="game-container">
      <h1>Dungeons and Databases</h1>

      <div className="player-stats">
        <h2>Player Stats</h2>
        <div className="stat">
          <span className="stat-label">Health:</span>
          <span className="stat-value">{player.health} HP</span>
        </div>
        <div className="stat">
          <span className="stat-label">Damage:</span>
          <span className="stat-value">{player.damage}</span>
        </div>
        <div className="stat">
          <span className="stat-label">Level:</span>
          <span className="stat-value">{player.level}</span>
        </div>
      </div>

      <button className="dungeon-button" onClick={handleDungeonClick}>
        Enter the Dungeon
      </button>
    </div>
  );
};

const Dungeon = () => {
  const [player, setPlayer] = useState({ health: 100, damage: 10, level: 1 });
  const [enemy, setEnemy] = useState({
    name: "",
    health: 0,
    max_health: 0,
    damage: 0,
    description: "",
  });
  const [message, setMessage] = useState(
    "You venture into the dark dungeon...",
  );
  const navigate = useNavigate();

  useEffect(() => {
    fetchPlayerStats();
    fetchCurrentEncounter();
  }, []);

  const fetchPlayerStats = async () => {
    try {
      const response = await fetch(`${API_BASE}/player`);
      const data = await response.json();
      setPlayer(data);
    } catch (error) {
      console.error("Error fetching player stats:", error);
    }
  };

  const fetchCurrentEncounter = async () => {
    try {
      const response = await fetch(`${API_BASE}/dungeon/encounter`);
      const data = await response.json();
      setEnemy(data);
      setMessage(`A wild ${data.name} appears! ${data.description}`);
    } catch (error) {
      console.error("Error fetching encounter:", error);
    }
  };

  const handleAttack = async () => {
    try {
      const response = await fetch(`${API_BASE}/dungeon/attack`, {
        method: "POST",
      });
      const data = await response.json();
      setPlayer(data.player);

      if (data.player_died) {
        setMessage(data.message || "You have been defeated!");
        // Redirect to home after showing death message
        setTimeout(() => {
          navigate("/");
        }, 3000);
      } else {
        setEnemy(data.enemy);
        setMessage(data.message || "You attacked the monster!");
      }
    } catch (error) {
      console.error("Error attacking:", error);
      setMessage("Failed to attack the monster.");
    }
  };

  const handleRunAway = async () => {
    try {
      const response = await fetch(`${API_BASE}/dungeon/run`, {
        method: "POST",
      });
      const data = await response.json();
      setPlayer(data.player);

      if (data.player_died) {
        setMessage(data.message || "You have been defeated!");
        // Redirect to home after showing death message
        setTimeout(() => {
          navigate("/");
        }, 3000);
      } else if (data.success) {
        // Successfully escaped - redirect to home
        setMessage(data.message || "You successfully escaped!");
        setTimeout(() => {
          navigate("/");
        }, 2000);
      } else {
        // Failed to escape - update enemy stats
        setEnemy(data.enemy);
        setMessage(data.message || "Failed to escape!");
      }
    } catch (error) {
      console.error("Error running away:", error);
      setMessage("Failed to escape.");
    }
  };

  return (
    <div className="game-container">
      <h1>The Dungeon</h1>

      <div style={{ marginTop: 20, fontSize: "1.2em", minHeight: 60 }}>
        <p>{message}</p>
      </div>

      <div
        style={{
          display: "flex",
          gap: 20,
          justifyContent: "center",
          flexWrap: "wrap",
          marginTop: 30,
        }}
      >
        <div
          className="player-stats"
          style={{ flex: "1", minWidth: "250px", maxWidth: "400px" }}
        >
          <h2>Player Stats</h2>
          <div className="stat">
            <span className="stat-label">Health:</span>
            <span className="stat-value">{player.health} HP</span>
          </div>
          <div className="stat">
            <span className="stat-label">Damage:</span>
            <span className="stat-value">{player.damage}</span>
          </div>
          <div className="stat">
            <span className="stat-label">Level:</span>
            <span className="stat-value">{player.level}</span>
          </div>
        </div>

        <div
          className="player-stats"
          style={{
            flex: "1",
            minWidth: "250px",
            maxWidth: "400px",
            borderColor: "#ff6b6b",
          }}
        >
          <h2 style={{ color: "#ff6b6b" }}>Enemy: {enemy?.name || "None"}</h2>
          {enemy && (
            <>
              <div className="stat">
                <span className="stat-label">Health:</span>
                <span className="stat-value">
                  {enemy.health} / {enemy.max_health} HP
                </span>
              </div>
              <div className="stat">
                <span className="stat-label">Damage:</span>
                <span className="stat-value">{enemy.damage}</span>
              </div>
            </>
          )}
        </div>
      </div>

      <div
        style={{
          marginTop: 40,
          display: "flex",
          gap: 10,
          justifyContent: "center",
          flexWrap: "wrap",
        }}
      >
        <button className="dungeon-button" onClick={handleAttack}>
          Attack
        </button>
        <button
          className="dungeon-button"
          style={{
            background: "linear-gradient(135deg, #ff9f1c 0%, #ffb700 100%)",
          }}
          onClick={handleRunAway}
        >
          Run Away
        </button>
      </div>
    </div>
  );
};

const App = () => {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/dungeon" element={<Dungeon />} />
      </Routes>
    </Router>
  );
};

export default App;
