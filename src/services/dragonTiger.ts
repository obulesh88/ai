import { DragonTigerRound } from '../types';

export interface DragonTigerStats {
  totalRounds: number;
  dragonWins: number;
  tigerWins: number;
  ties: number;
  dragonPct: number;
  tigerPct: number;
  tiePct: number;
  currentStreak: {
    winner: 'dragon' | 'tiger' | 'tie';
    count: number;
  };
  longestStreak: {
    dragon: number;
    tiger: number;
  };
  prediction: {
    recommended: 'dragon' | 'tiger';
    confidence: number;
    reasoning: string;
    kellyFraction: number;
  };
  bigRoad: Array<Array<{ winner: 'dragon' | 'tiger' | 'tie'; tiesCount: number }>>;
}

const SUITS = ['♠', '♥', '♦', '♣'];
const RANKS = [
  { rank: 'A', value: 1 },
  { rank: '2', value: 2 },
  { rank: '3', value: 3 },
  { rank: '4', value: 4 },
  { rank: '5', value: 5 },
  { rank: '6', value: 6 },
  { rank: '7', value: 7 },
  { rank: '8', value: 8 },
  { rank: '9', value: 9 },
  { rank: '10', value: 10 },
  { rank: 'J', value: 11 },
  { rank: 'Q', value: 12 },
  { rank: 'K', value: 13 },
];

export function generateRandomCard() {
  const r = RANKS[Math.floor(Math.random() * RANKS.length)];
  const s = SUITS[Math.floor(Math.random() * SUITS.length)];
  return { rank: r.rank, value: r.value, suit: s };
}

export function playRound(roundId: number): DragonTigerRound {
  const dragonCard = generateRandomCard();
  const tigerCard = generateRandomCard();
  let winner: 'dragon' | 'tiger' | 'tie' = 'tie';
  if (dragonCard.value > tigerCard.value) {
    winner = 'dragon';
  } else if (tigerCard.value > dragonCard.value) {
    winner = 'tiger';
  }

  return {
    id: roundId,
    dragonCard,
    tigerCard,
    winner,
    timestamp: new Date().toLocaleTimeString(),
  };
}

export function computeStats(rounds: DragonTigerRound[]): DragonTigerStats {
  const total = rounds.length;
  if (total === 0) {
    return {
      totalRounds: 0,
      dragonWins: 0,
      tigerWins: 0,
      ties: 0,
      dragonPct: 0,
      tigerPct: 0,
      tiePct: 0,
      currentStreak: { winner: 'dragon', count: 0 },
      longestStreak: { dragon: 0, tiger: 0 },
      prediction: {
        recommended: 'dragon',
        confidence: 50,
        reasoning: 'No shoe history. Neutral 50/50 prior.',
        kellyFraction: 0,
      },
      bigRoad: [],
    };
  }

  let dragonWins = 0;
  let tigerWins = 0;
  let ties = 0;
  let maxDragonStreak = 0;
  let maxTigerStreak = 0;
  let currentDragonStreak = 0;
  let currentTigerStreak = 0;

  let currentStreakWinner: 'dragon' | 'tiger' | 'tie' = rounds[rounds.length - 1].winner;
  let currentStreakCount = 0;

  for (let i = rounds.length - 1; i >= 0; i--) {
    if (rounds[i].winner === currentStreakWinner) {
      currentStreakCount++;
    } else {
      break;
    }
  }

  for (const r of rounds) {
    if (r.winner === 'dragon') {
      dragonWins++;
      currentDragonStreak++;
      currentTigerStreak = 0;
      if (currentDragonStreak > maxDragonStreak) maxDragonStreak = currentDragonStreak;
    } else if (r.winner === 'tiger') {
      tigerWins++;
      currentTigerStreak++;
      currentDragonStreak = 0;
      if (currentTigerStreak > maxTigerStreak) maxTigerStreak = currentTigerStreak;
    } else {
      ties++;
      // In casino analytics, ties don't break main shoe columns but are tallied
    }
  }

  // Calculate Big Road columns
  const bigRoad: Array<Array<{ winner: 'dragon' | 'tiger' | 'tie'; tiesCount: number }>> = [];
  let currentCol: Array<{ winner: 'dragon' | 'tiger' | 'tie'; tiesCount: number }> = [];
  let lastNonTieWinner: 'dragon' | 'tiger' | null = null;
  let pendingTies = 0;

  for (const r of rounds) {
    if (r.winner === 'tie') {
      if (currentCol.length > 0) {
        currentCol[currentCol.length - 1].tiesCount++;
      } else {
        pendingTies++;
      }
      continue;
    }

    if (!lastNonTieWinner) {
      lastNonTieWinner = r.winner;
      currentCol.push({ winner: r.winner, tiesCount: pendingTies });
      pendingTies = 0;
    } else if (r.winner === lastNonTieWinner) {
      currentCol.push({ winner: r.winner, tiesCount: pendingTies });
      pendingTies = 0;
    } else {
      bigRoad.push(currentCol);
      currentCol = [{ winner: r.winner, tiesCount: pendingTies }];
      lastNonTieWinner = r.winner;
      pendingTies = 0;
    }
  }
  if (currentCol.length > 0) {
    bigRoad.push(currentCol);
  }

  // Prediction model based on streak clustering and mean reversion
  const nonTieCount = dragonWins + tigerWins;
  const dRatio = nonTieCount ? dragonWins / nonTieCount : 0.5;
  let recommended: 'dragon' | 'tiger' = 'dragon';
  let confidence = 50;
  let reasoning = '';

  if (currentStreakWinner !== 'tie' && currentStreakCount >= 4) {
    // Mean reversion probability increases when streak > 4
    recommended = currentStreakWinner === 'dragon' ? 'tiger' : 'dragon';
    confidence = Math.min(68, 52 + currentStreakCount * 3.5);
    reasoning = `High streak detected (${currentStreakCount} consecutive ${currentStreakWinner.toUpperCase()}). Historical mean-reversion favored.`;
  } else if (dRatio > 0.55) {
    recommended = 'tiger';
    confidence = 54.5;
    reasoning = `Dragon imbalance in shoe (${(dRatio * 100).toFixed(1)}%). Reversion towards 50/50 balance expected.`;
  } else if (dRatio < 0.45) {
    recommended = 'dragon';
    confidence = 54.5;
    reasoning = `Tiger imbalance in shoe (${((1 - dRatio) * 100).toFixed(1)}%). Reversion towards 50/50 balance expected.`;
  } else {
    recommended = currentStreakWinner === 'tiger' ? 'tiger' : 'dragon';
    confidence = 51.5;
    reasoning = 'Shoe distribution balanced. Following prevailing Big Road column momentum.';
  }

  // Kelly Criterion fraction (b * p - q) / b
  const b = 1.0;
  const p = confidence / 100;
  const q = 1 - p;
  const kellyFraction = Math.max(0, (b * p - q) / b);

  return {
    totalRounds: total,
    dragonWins,
    tigerWins,
    ties,
    dragonPct: total ? Number(((dragonWins / total) * 100).toFixed(1)) : 0,
    tigerPct: total ? Number(((tigerWins / total) * 100).toFixed(1)) : 0,
    tiePct: total ? Number(((ties / total) * 100).toFixed(1)) : 0,
    currentStreak: {
      winner: currentStreakWinner,
      count: currentStreakCount,
    },
    longestStreak: {
      dragon: maxDragonStreak,
      tiger: maxTigerStreak,
    },
    prediction: {
      recommended,
      confidence: Number(confidence.toFixed(1)),
      reasoning,
      kellyFraction: Number((kellyFraction * 0.25).toFixed(3)), // Fractional Kelly 1/4 for bankroll preservation
    },
    bigRoad,
  };
}

export function generateInitialShoe(): DragonTigerRound[] {
  const rounds: DragonTigerRound[] = [];
  for (let i = 1; i <= 36; i++) {
    rounds.push(playRound(i));
  }
  return rounds;
}
