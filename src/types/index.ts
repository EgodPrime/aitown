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
}

export interface IAction {
  type: string;
  description?: string;
  changes?: Record<string, any>;
}