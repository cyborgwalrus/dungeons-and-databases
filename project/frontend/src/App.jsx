import { useState, useEffect } from "react";
import {
  BrowserRouter as Router,
  Routes,
  Route,
  useNavigate,
} from "react-router-dom";
import "./App.css";

const API_BASE = import.meta.env.VITE_API_BASE || "http://localhost:5000/api";

const Inventory = ({ items }) => {
  return (
    <div className="inventory-panel">
      <h3>🎒 Inventory {items && items.length > 0 && `(${items.length})`}</h3>
      {!items || items.length === 0 ? (
        <div style={{
          padding: "20px",
          textAlign: "center",
          backgroundColor: "rgba(0, 0, 0, 0.2)",
          borderRadius: "8px",
          marginTop: "10px"
        }}>
          <p style={{ color: "#999", fontStyle: "italic", marginBottom: "10px", fontSize: "1.1em" }}>
            🎒 Your inventory is empty
          </p>
          <p style={{ color: "#666", fontSize: "0.9em", marginBottom: 0 }}>
            Defeat enemies in the dungeon to collect items and equipment!
          </p>
        </div>
      ) : (
        <div className="inventory-list">
          {items.map((invItem) => (
            <div key={invItem.id} className="inventory-item">
              <span className="item-icon">
                {invItem.item.bonus_attack > 0 && invItem.item.bonus_health === 0 && "⚔️"}
                {invItem.item.bonus_health > 0 && invItem.item.bonus_attack === 0 && "🛡️"}
                {invItem.item.bonus_health > 0 && invItem.item.bonus_attack > 0 && "💎"}
                {invItem.item.bonus_health === 0 && invItem.item.bonus_attack === 0 && "💰"}
              </span>
              <div className="item-details">
                <p className="item-name">{invItem.item.name}</p>
                <p className="item-type">+{invItem.item.bonus_health}HP / +{invItem.item.bonus_attack}ATK</p>
              </div>
              <span className="item-quantity">×{invItem.quantity}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

const Home = () => {
  const [player, setPlayer] = useState({ health: 100, damage: 10, level: 1, bonus_health: 0, bonus_damage: 0 });
  const [inventory, setInventory] = useState([]);
  const [equipped, setEquipped] = useState([]);
  const [allItems, setAllItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showEquipMenu, setShowEquipMenu] = useState(true);
  const [showAvailable, setShowAvailable] = useState(false);
  const navigate = useNavigate();

  useEffect(() => {
    fetchPlayerStats();
    fetchInventory();
    fetchEquipped();
    fetchAllItems();
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

  const fetchInventory = async () => {
    try {
      const response = await fetch(`${API_BASE}/inventory`);
      const data = await response.json();
      setInventory(data);
    } catch (error) {
      console.error("Error fetching inventory:", error);
    }
  };

  const fetchEquipped = async () => {
    try {
      const response = await fetch(`${API_BASE}/inventory/equipped`);
      const data = await response.json();
      setEquipped(data);
    } catch (error) {
      console.error("Error fetching equipped:", error);
    }
  };

  const fetchAllItems = async () => {
    try {
      const response = await fetch(`${API_BASE}/inventory/items`);
      const data = await response.json();
      setAllItems(data);
    } catch (error) {
      console.error("Error fetching items:", error);
    }
  };

  const handleEquipItem = async (itemId, slot) => {
    try {
      const response = await fetch(`${API_BASE}/inventory/equip`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ item_id: itemId, slot }),
      });
      const data = await response.json();
      if (response.ok) {
        setPlayer(data.player);
        fetchEquipped();
        fetchAllItems();
      }
    } catch (error) {
      console.error("Error equipping item:", error);
    }
  };

  const handleUnequipItem = async (slot) => {
    try {
      const response = await fetch(`${API_BASE}/inventory/unequip/${slot}`, {
        method: "DELETE",
      });
      const data = await response.json();
      if (response.ok) {
        setPlayer(data.player);
        fetchEquipped();
        fetchAllItems();
      }
    } catch (error) {
      console.error("Error unequipping item:", error);
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
        {player.bonus_health > 0 && (
          <div className="stat" style={{ color: "#4ecdc4" }}>
            <span className="stat-label">+Health Bonus:</span>
            <span className="stat-value">+{player.bonus_health}</span>
          </div>
        )}
        {player.bonus_damage > 0 && (
          <div className="stat" style={{ color: "#4ecdc4" }}>
            <span className="stat-label">+Attack Bonus:</span>
            <span className="stat-value">+{player.bonus_damage}</span>
          </div>
        )}
      </div>

      <div style={{ marginTop: 30 }}>
        <h3 style={{ marginBottom: 15, cursor: "pointer", color: "#4ecdc4" }} onClick={() => setShowEquipMenu(!showEquipMenu)}>
          {showEquipMenu ? "▼" : "▶"} Equipment ({equipped.length}/5 Slots)
        </h3>
        
        {showEquipMenu && (
          <div style={{
            background: "rgba(0, 0, 0, 0.3)",
            border: "2px solid #4ecdc4",
            borderRadius: "10px",
            padding: "20px",
            marginBottom: "20px"
          }}>
            <div style={{ marginBottom: "20px" }}>
              <h4 style={{ marginTop: 0, color: "#4ecdc4" }}>Equipped Items:</h4>
              <div style={{ display: "grid", gridTemplateColumns: "repeat(5, 1fr)", gap: "10px" }}>
                {Array.from({ length: 5 }).map((_, slotNum) => {
                  const equippedInSlot = equipped.find(eq => eq.slot === slotNum);
                  return (
                    <div key={slotNum} style={{
                      background: equippedInSlot ? "rgba(78, 205, 196, 0.2)" : "rgba(0, 0, 0, 0.5)",
                      border: "2px solid #4ecdc4",
                      borderRadius: "5px",
                      padding: "10px",
                      textAlign: "center",
                      minHeight: "100px",
                      display: "flex",
                      flexDirection: "column",
                      justifyContent: "space-between"
                    }}>
                      <span style={{ fontSize: "0.9em", color: "#999" }}>Slot {slotNum + 1}</span>
                      {equippedInSlot ? (
                        <>
                          <div>
                            <p style={{ margin: "5px 0", fontWeight: "bold", color: "#4ecdc4" }}>
                              {equippedInSlot.item.name}
                            </p>
                            <p style={{ margin: "2px 0", fontSize: "0.85em" }}>
                              +{equippedInSlot.item.bonus_health}HP / +{equippedInSlot.item.bonus_attack}ATK
                            </p>
                          </div>
                          <button
                            onClick={() => handleUnequipItem(slotNum)}
                            style={{
                              background: "#ff6b6b",
                              color: "white",
                              border: "none",
                              padding: "5px",
                              borderRadius: "3px",
                              cursor: "pointer",
                              fontSize: "0.8em"
                            }}
                          >
                            Unequip
                          </button>
                        </>
                      ) : (
                        <span style={{ color: "#999", fontSize: "0.9em" }}>Empty</span>
                      )}
                    </div>
                  );
                })}
              </div>
            </div>

            <hr style={{ opacity: 0.3, margin: "20px 0" }} />

            <h4 style={{ marginTop: 0, color: "#4ecdc4", cursor: "pointer" }} onClick={() => setShowAvailable(!showAvailable)}>
              {showAvailable ? "▼" : "▶"} Available Items ({inventory.length})
            </h4>

            {showAvailable && (
              <div style={{ display: "flex", flexDirection: "column", gap: "10px", maxHeight: "300px", overflowY: "auto" }}>
                {allItems && allItems.length > 0 ? (
                  allItems.map((item, idx) => (
                    <div key={idx} style={{
                      background: "rgba(0, 0, 0, 0.5)",
                      border: "1px solid #4ecdc4",
                      borderRadius: "5px",
                      padding: "10px",
                      display: "flex",
                      justifyContent: "space-between",
                      alignItems: "center"
                    }}>
                      <div style={{ flex: 1 }}>
                        <p style={{ margin: 0, fontWeight: "bold", color: "#4ecdc4" }}>
                          {item.item.name}
                        </p>
                        <p style={{ margin: "5px 0", fontSize: "0.9em", color: "#999" }}>
                          +{item.item.bonus_health} HP / +{item.item.bonus_attack} ATK | Qty: {item.quantity}
                        </p>
                      </div>
                      <button
                        onClick={() => handleEquipItem(item.item.id, equipped.length < 5 ? equipped.length : 0)}
                        style={{
                          background: item.equipped ? "#999" : "#4ecdc4",
                          color: "white",
                          border: "none",
                          padding: "8px 12px",
                          borderRadius: "3px",
                          cursor: "pointer",
                          marginLeft: "10px",
                          whiteSpace: "nowrap"
                        }}
                        disabled={item.equipped}
                      >
                        {item.equipped ? "Equipped" : "Equip"}
                      </button>
                    </div>
                  ))
                ) : (
                  <p style={{ color: "#999", fontStyle: "italic" }}>No items in inventory</p>
                )}
              </div>
            )}
          </div>
        )}
      </div>

      <div style={{ marginBottom: "20px", display: "flex", gap: "10px", justifyContent: "center", flexWrap: "wrap" }}>
        <button className="dungeon-button" onClick={handleDungeonClick}>
          Enter the Dungeon
        </button>
      </div>
    </div>
  );
};

const Dungeon = () => {
  const [player, setPlayer] = useState({ health: 100, damage: 10, level: 1, bonus_health: 0, bonus_damage: 0 });
  const [inventory, setInventory] = useState([]);
  const [equipped, setEquipped] = useState([]);
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
  const [itemsDropped, setItemsDropped] = useState([]);
  const navigate = useNavigate();

  useEffect(() => {
    fetchPlayerStats();
    fetchCurrentEncounter();
    fetchInventory();
    fetchEquipped();
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

  const fetchInventory = async () => {
    try {
      const response = await fetch(`${API_BASE}/inventory`);
      const data = await response.json();
      setInventory(data);
    } catch (error) {
      console.error("Error fetching inventory:", error);
    }
  };

  const fetchEquipped = async () => {
    try {
      const response = await fetch(`${API_BASE}/inventory/equipped`);
      const data = await response.json();
      setEquipped(data);
    } catch (error) {
      console.error("Error fetching equipped:", error);
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
        setItemsDropped(data.items_dropped || []);
        // Refresh inventory after combat
        fetchInventory();
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

  const handleBackToHome = () => {
    navigate("/");
  };

  return (
    <div className="game-container">
      <h1>The Dungeon</h1>

      <div style={{ marginTop: 20, fontSize: "1.2em", minHeight: 60 }}>
        <p>{message}</p>
        {itemsDropped.length > 0 && (
          <div
            style={{
              marginTop: 10,
              padding: 10,
              backgroundColor: "#2d3436",
              borderLeft: "4px solid #fdcb6e",
              borderRadius: 4,
            }}
          >
            <strong style={{ color: "#fdcb6e" }}>🎁 Loot obtained:</strong>
            <p>
              {itemsDropped.map((item) => item.name).join(", ")}
            </p>
          </div>
        )}
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
          {player.bonus_health > 0 && (
            <div className="stat" style={{ color: "#4ecdc4" }}>
              <span className="stat-label">+Health Bonus:</span>
              <span className="stat-value">+{player.bonus_health}</span>
            </div>
          )}
          {player.bonus_damage > 0 && (
            <div className="stat" style={{ color: "#4ecdc4" }}>
              <span className="stat-label">+Attack Bonus:</span>
              <span className="stat-value">+{player.bonus_damage}</span>
            </div>
          )}
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
        <button
          className="dungeon-button"
          style={{
            background: "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
          }}
          onClick={handleBackToHome}
        >
          Back to Home
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
