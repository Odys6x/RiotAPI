import React, { useEffect, useState } from 'react';
import { TrendingUp, TrendingDown } from 'lucide-react';

const GameOverlay = () => {
  const [gameData, setGameData] = useState({
    orderTeam: {
      gold: 0,
      kills: 0,
      deaths: 0,
      assists: 0,
      cs: 0,
      players: []
    },
    chaosTeam: {
      gold: 0,
      kills: 0,
      deaths: 0,
      assists: 0,
      cs: 0,
      players: []
    },
    winProbability: {
      order: 50,
      chaos: 50
    }
  });

  useEffect(() => {
    // Add to window object to allow Python to update data
    window.updateGameData = (data) => {
      setGameData(data);
    };

    // Polling fallback if needed
    const pollData = async () => {
      try {
        const response = await fetch('http://localhost:8000/api/game-data');
        const data = await response.json();
        setGameData(data);
      } catch (error) {
        console.error('Error fetching game data:', error);
      }
    };

    const interval = setInterval(pollData, 1000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="w-full max-w-5xl bg-black/40 backdrop-blur-sm rounded-lg p-4 text-white">
      {/* Win Probability Bar */}
      <div className="h-2 bg-gray-700 rounded-full overflow-hidden mb-4">
        <div
          className="h-full bg-gradient-to-r from-blue-500 to-blue-400"
          style={{ width: `${gameData.winProbability.order}%` }}
        />
      </div>

      <div className="grid grid-cols-3 gap-4">
        {/* ORDER Team Stats */}
        <div className="bg-blue-500/20 border border-blue-500/50 rounded-lg">
          <div className="p-4">
            <div className="flex justify-between items-center mb-2">
              <h3 className="text-lg font-bold text-blue-400">ORDER</h3>
              <div className="flex items-center gap-2">
                <span className="text-sm">{gameData.winProbability.order}%</span>
                <TrendingUp className="h-4 w-4 text-green-400" />
              </div>
            </div>
            <div className="space-y-2">
              {gameData.orderTeam.players.map((player, index) => (
                <div key={index} className="bg-blue-500/10 rounded p-2 text-sm">
                  <div className="flex justify-between items-center">
                    <div className="flex items-center gap-2">
                      <div className="w-6 h-6 bg-blue-500/30 rounded-full flex items-center justify-center text-xs">
                        {player.champion?.charAt(0)}
                      </div>
                      <span className="font-medium">{player.champion}</span>
                    </div>
                    <span>{player.kills}/{player.deaths}/{player.assists}</span>
                  </div>
                  <div className="flex justify-between text-xs mt-1 opacity-80">
                    <span>CS: {player.cs}</span>
                    <span>{(player.gold / 1000).toFixed(1)}k</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Central Stats Panel */}
        <div className="bg-gray-800/60 border border-gray-700 rounded-lg">
          <div className="p-4">
            <div className="space-y-4">
              {/* Gold Difference */}
              <div>
                <h4 className="text-center text-sm mb-1">Gold Difference</h4>
                <div className="relative h-2 bg-gray-700 rounded-full overflow-hidden">
                  <div
                    className="absolute h-full bg-gradient-to-r from-blue-500 to-blue-400"
                    style={{
                      width: `${(gameData.orderTeam.gold / (gameData.orderTeam.gold + gameData.chaosTeam.gold)) * 100}%`
                    }}
                  />
                </div>
                <div className="flex justify-between text-xs mt-1">
                  <span>{(gameData.orderTeam.gold / 1000).toFixed(1)}k</span>
                  <span>{(gameData.chaosTeam.gold / 1000).toFixed(1)}k</span>
                </div>
              </div>

              {/* Team KDA Comparison */}
              <div className="grid grid-cols-3 gap-2 text-center">
                <div>
                  <div className="text-xl font-bold">{gameData.orderTeam.kills}</div>
                  <div className="text-xs opacity-70">Kills</div>
                </div>
                <div>
                  <div className="text-xl font-bold">{gameData.orderTeam.deaths}</div>
                  <div className="text-xs opacity-70">Deaths</div>
                </div>
                <div>
                  <div className="text-xl font-bold">{gameData.orderTeam.assists}</div>
                  <div className="text-xs opacity-70">Assists</div>
                </div>
              </div>

              {/* CS Difference */}
              <div>
                <h4 className="text-center text-sm mb-1">CS Difference</h4>
                <div className="relative h-2 bg-gray-700 rounded-full overflow-hidden">
                  <div
                    className="absolute h-full bg-gradient-to-r from-blue-500 to-blue-400"
                    style={{
                      width: `${(gameData.orderTeam.cs / (gameData.orderTeam.cs + gameData.chaosTeam.cs)) * 100}%`
                    }}
                  />
                </div>
                <div className="flex justify-between text-xs mt-1">
                  <span>{gameData.orderTeam.cs}</span>
                  <span>{gameData.chaosTeam.cs}</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* CHAOS Team Stats */}
        <div className="bg-red-500/20 border border-red-500/50 rounded-lg">
          <div className="p-4">
            <div className="flex justify-between items-center mb-2">
              <h3 className="text-lg font-bold text-red-400">CHAOS</h3>
              <div className="flex items-center gap-2">
                <span className="text-sm">{gameData.winProbability.chaos}%</span>
                <TrendingDown className="h-4 w-4 text-red-400" />
              </div>
            </div>
            <div className="space-y-2">
              {gameData.chaosTeam.players.map((player, index) => (
                <div key={index} className="bg-red-500/10 rounded p-2 text-sm">
                  <div className="flex justify-between items-center">
                    <div className="flex items-center gap-2">
                      <div className="w-6 h-6 bg-red-500/30 rounded-full flex items-center justify-center text-xs">
                        {player.champion?.charAt(0)}
                      </div>
                      <span className="font-medium">{player.champion}</span>
                    </div>
                    <span>{player.kills}/{player.deaths}/{player.assists}</span>
                  </div>
                  <div className="flex justify-between text-xs mt-1 opacity-80">
                    <span>CS: {player.cs}</span>
                    <span>{(player.gold / 1000).toFixed(1)}k</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default GameOverlay;