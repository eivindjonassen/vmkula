
import React from 'react';
import { GroupData, TeamPrediction } from '../types';

interface GroupCardProps {
  group: GroupData;
  predictions?: TeamPrediction[];
}

const GroupCard: React.FC<GroupCardProps> = ({ group, predictions }) => {
  const hosts = ['Mexico', 'Canada', 'USA'];

  const getPrediction = (teamId: number) => {
    return predictions?.find(p => p.teamId === teamId);
  };

  // Sorterer lagene dynamisk: 
  // 1. Poeng (høyest først)
  // 2. AI-rangering (lavest tall først, f.eks. #1 er bedre enn #2)
  const sortedTeams = [...group.teams].sort((a, b) => {
    if (b.points !== a.points) {
      return b.points - a.points;
    }
    
    const predA = getPrediction(a.id);
    const predB = getPrediction(b.id);
    
    // Hvis AI-analyse mangler, legges de nederst (rank 99)
    const rankA = predA ? predA.rank : 99;
    const rankB = predB ? predB.rank : 99;
    
    return rankA - rankB;
  });

  return (
    <div className="bg-white rounded-[2.5rem] shadow-xl border border-slate-200 overflow-hidden transition-all hover:shadow-2xl hover:border-blue-100">
      {/* Header */}
      <div className="bg-slate-900 px-8 py-6 flex justify-between items-center border-b border-white/5 relative overflow-hidden">
        <div className="absolute top-0 right-0 w-48 h-48 bg-blue-600/10 rounded-full blur-3xl -mr-16 -mt-16"></div>
        <div className="flex items-center gap-5 relative z-10">
          <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-blue-500 to-indigo-600 flex items-center justify-center text-white font-black text-3xl shadow-lg shadow-blue-500/20">
            {group.id}
          </div>
          <div>
            <h3 className="text-white font-black text-2xl tracking-tight">{group.name}</h3>
            <p className="text-[10px] text-blue-400 font-bold uppercase tracking-[0.2em]">Offisielt Gruppeoppsett</p>
          </div>
        </div>
        <div className="hidden sm:flex items-center gap-2 bg-white/5 px-4 py-2 rounded-full border border-white/10 relative z-10">
            <span className="w-2 h-2 rounded-full bg-blue-500 animate-pulse"></span>
            <span className="text-[9px] text-slate-300 font-black uppercase tracking-widest">Live AI Analysis</span>
        </div>
      </div>

      {/* Table */}
      <div className="overflow-x-auto">
        <table className="w-full text-sm text-left border-collapse">
          <thead>
            <tr className="bg-slate-50/50">
              <th className="pl-8 pr-2 py-5 text-center text-[10px] font-black text-slate-400 uppercase tracking-widest border-b border-slate-100 w-16">Pos</th>
              <th className="px-4 py-5 text-[10px] font-black text-slate-500 uppercase tracking-widest border-b border-slate-100">Nasjon & Prediksjon</th>
              <th className="px-4 py-5 text-center text-[10px] font-black text-slate-500 uppercase tracking-widest border-b border-slate-100 w-16">S</th>
              <th className="px-4 py-5 text-center text-[10px] font-black text-slate-500 uppercase tracking-widest border-b border-slate-100 w-16">MF</th>
              <th className="px-8 py-5 text-center text-[10px] font-black text-blue-600 uppercase tracking-widest border-b border-slate-100 w-28">Poeng</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {sortedTeams.map((team, idx) => {
              const pred = getPrediction(team.id);
              const isPlaceholder = team.name.toLowerCase().includes('vinner') || team.name.toLowerCase().includes('playoff');
              const isAdvancing = idx < 2;

              return (
                <tr key={team.id} className={`${isAdvancing ? 'bg-blue-50/10' : ''} hover:bg-slate-50/80 transition-all group cursor-default`}>
                  {/* Posisjon i tabellen (Nåværende basert på sortering) */}
                  <td className="pl-8 pr-2 py-6 text-center">
                    <span className={`text-base font-black ${isAdvancing ? 'text-blue-600' : 'text-slate-400'}`}>
                      {idx + 1}
                    </span>
                  </td>

                  {/* Nasjon og AI Info */}
                  <td className="px-4 py-6">
                    <div className="flex items-start gap-5">
                      <div className="text-5xl filter drop-shadow-md group-hover:scale-110 transition-transform duration-300 flex-shrink-0">
                        {team.flag}
                      </div>
                      <div className="flex flex-col gap-1.5 min-w-0">
                        <div className="flex flex-wrap items-center gap-2">
                            <span className={`font-black text-xl tracking-tight truncate transition-colors ${
                              isPlaceholder ? 'text-slate-400 italic font-bold' : 'text-slate-900 group-hover:text-blue-600'
                            }`}>
                              {team.name}
                            </span>
                            
                            {/* Predikert Plassering Badge */}
                            {pred && (
                                <span className={`text-[9px] font-black px-2 py-0.5 rounded-md border shadow-sm flex items-center gap-1 ${
                                    pred.rank === 1 ? 'bg-amber-100 text-amber-700 border-amber-200' : 
                                    pred.rank === 2 ? 'bg-slate-100 text-slate-700 border-slate-200' :
                                    'bg-blue-50 text-blue-700 border-blue-100'
                                }`}>
                                    <span className="opacity-70">🤖 AI:</span> #{pred.rank}
                                </span>
                            )}

                            {hosts.includes(team.name) && (
                                <span className="text-[8px] font-black text-white uppercase bg-blue-600 px-1.5 py-0.5 rounded shadow-sm">
                                    Vert
                                </span>
                            )}
                        </div>

                        {/* AI Tips / Analyse */}
                        {pred && (
                            <div className="bg-slate-50/50 p-2.5 rounded-xl border border-slate-100/50 max-w-sm group-hover:border-blue-100 transition-colors">
                                <p className="text-[11px] font-medium text-slate-600 leading-relaxed italic">
                                    <span className="font-black text-blue-500 uppercase text-[9px] not-italic tracking-wider mr-1">AI Tips:</span>
                                    {pred.note}
                                </p>
                            </div>
                        )}
                      </div>
                    </div>
                  </td>

                  {/* Statistikk-kolonner */}
                  <td className="px-4 py-6 text-center text-slate-400 font-black text-base tabular-nums">{team.played}</td>
                  <td className="px-4 py-6 text-center text-slate-400 font-black text-base tabular-nums">
                    {team.goalsFor - team.goalsAgainst}
                  </td>

                  {/* Poeng-kolonne */}
                  <td className="px-8 py-6 text-center">
                      <div className="relative inline-block group-hover:scale-110 transition-transform">
                        <span className={`inline-block w-14 h-14 rounded-2xl ${isAdvancing ? 'bg-blue-600 text-white shadow-lg shadow-blue-200' : 'bg-slate-100 text-slate-400'} font-black flex items-center justify-center text-2xl border border-transparent`}>
                            {team.points}
                        </span>
                        {/* Status-glimt */}
                        {isAdvancing && (
                            <div className="absolute -top-1 -right-1 w-3 h-3 bg-green-500 border-2 border-white rounded-full"></div>
                        )}
                      </div>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      {/* Footer / Forklaring */}
      <div className="bg-slate-50/80 backdrop-blur-sm px-8 py-5 flex justify-between items-center border-t border-slate-100">
        <div className="flex items-center gap-6">
            <div className="flex items-center gap-2">
                <span className="w-2.5 h-2.5 rounded-full bg-blue-500 shadow-sm shadow-blue-200"></span>
                <span className="text-[10px] font-black text-slate-500 uppercase tracking-widest">Videre</span>
            </div>
            <div className="flex items-center gap-2">
                <span className="w-2.5 h-2.5 rounded-full bg-slate-200"></span>
                <span className="text-[10px] font-black text-slate-400 uppercase tracking-widest">Ute</span>
            </div>
        </div>
        <div className="flex flex-col items-end">
            <span className="text-[10px] text-slate-400 font-black uppercase tracking-widest">Data Simulation v2.6</span>
            <span className="text-[8px] text-blue-400 font-bold uppercase tracking-tight">AI-drevet sortering aktivert</span>
        </div>
      </div>
    </div>
  );
};

export default GroupCard;
