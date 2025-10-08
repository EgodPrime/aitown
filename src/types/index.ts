export interface INPC {
  id: string;
  player_id: string;
  name: string;
  prompt: string;
  hunger: number;
  energy: number;
  mood: number;
  money: number;
  inventory: Record<string, number>;
  location: string;
  alive: boolean;
  memory_log: IMemoryLog;
  transactions: ITransaction[];
}

export interface IAction {
  type: string;
  description?: string;
  changes?: Record<string, any>;
}

export interface IMemoryEntry {
  timestamp: string;
  content: string;
}

export interface IMemoryLog {
  recent_memory: IMemoryEntry[];
  old_memory: string;
}

export interface ITransaction {
  id: string;
  type: string;
  summary: string;
}