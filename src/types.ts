export interface Chart {
  type: 'bar' | 'line';
  data: {
    labels: string[];
    values: number[];
  };
}