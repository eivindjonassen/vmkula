
import React, { useState, useEffect, useMemo } from 'react';
import { INITIAL_GROUPS, MATCHES, VENUES, STAGES } from './constants';
import { AIAnalysis, Match, GroupData, MatchPrediction } from './types';
import { getWorldCupAnalysis } from './services/geminiService';
import GroupCard from './components/GroupCard';

type Tab = 'tables' | 'matches' | 'venues';

const App: React.FC = () => {
  const [activeTab, setActiveTab] = useState<Tab>('tables');
  const [analysis, setAnalysis] = useState<AIAnalysis | null>(null);
  const [loadingAnalysis, setLoadingAnalysis] = useState(true);
  const [selectedStage, setSelectedStage] = useState<number | 'all'>('all');
  const [hidePast, setHidePast] = useState(false);

  const now = useMemo(() => new Date(), []);

  const parseKickoff = (kickoff: string) => {
    let normalized = kickoff.replace(' ', 'T');
    if (normalized.match(/-\d{2}$/)) normalized += ':00';
    const date = new Date(normalized);
    return isNaN(date.getTime()) ? null : date;
  };

  useEffect(() => {
    const fetchAnalysis = async () => {
      try {
        const data = await getWorldCupAnalysis();
        setAnalysis(data);
      } catch (err) {
        console.error("Error fetching WC analysis:", err);
      } finally {
        setLoadingAnalysis(false);
      }
    };
    fetchAnalysis();
  }, []);

  const allTeams = useMemo(() => {
    const teamsMap: Record<number, any> = {};
    INITIAL_GROUPS.forEach(g => {
      g.teams.forEach(t => {
        teamsMap[t.id] = t;
      });
    });
    return teamsMap;
  }, []);

  const getMatchPrediction = (match: Match): MatchPrediction | undefined => {
    const pathEntry = analysis?.tournamentPath?.find(p => p.matchNumber === match.matchNumber);
    
    // Sluttspill-logikk for TBD kamper
    if (!match.homeTeamId || !match.awayTeamId) {
        if (pathEntry) {
            const isHomeWinner = pathEntry.winnerLabel === pathEntry.homeLabel;
            return {
                winnerId: null,
                winProbability: isHomeWinner ? 65 : 35,
                reasoning: `AI spår at ${pathEntry.winnerLabel} vinner dette oppgjøret og går videre i turneringen.`,
                predictedHomeScore: pathEntry.predictedHomeScore,
                predictedAwayScore: pathEntry.predictedAwayScore,
                predictedHomeTeamLabel: pathEntry.homeLabel,
                predictedAwayTeamLabel: pathEntry.awayLabel,
                predictedWinnerLabel: pathEntry.winnerLabel
            };
        }
        return {
            winnerId: null,
            winProbability: 50,
            reasoning: "Venter på gruppeavklaring.",
            predictedHomeScore: 0,
            predictedAwayScore: 0
        };
    }

    // Gruppespill-logikk
    const h = allTeams[match.homeTeamId];
    const a = allTeams[match.awayTeamId];
    const hPred = analysis?.groupPredictions?.flatMap(gp => gp.predictions).find(p => p.teamId === match.homeTeamId);
    const aPred = analysis?.groupPredictions?.flatMap(gp => gp.predictions).find(p => p.teamId === match.awayTeamId);
    
    let prob = 50;
    if (hPred && aPred) {
        const diff = aPred.rank - hPred.rank;
        prob = 50 + (diff * 12);
        prob = Math.max(15, Math.min(85, prob));
    }
    
    return {
        winnerId: prob > 50 ? match.homeTeamId : match.awayTeamId,
        winProbability: prob > 50 ? prob : 100 - prob,
        reasoning: hPred?.note ? `${h?.name}: ${hPred.note}` : `Statistisk fordel til ${prob > 50 ? h?.name : a?.name}.`,
        predictedHomeScore: prob > 60 ? 2 : prob > 40 ? 1 : 0,
        predictedAwayScore: prob < 40 ? 2 : prob < 60 ? 1 : 0
    };
  };

  const filteredMatches = useMemo(() => {
    let matches = [...MATCHES];
    if (selectedStage !== 'all') matches = matches.filter(m => m.stageId === selectedStage);
    if (hidePast) {
      matches = matches.filter(m => {
        const kd = parseKickoff(m.kickoff);
        return kd && kd.getTime() + (2 * 60 * 60 * 1000) > now.getTime();
      });
    }
    return matches.sort((a, b) => (parseKickoff(a.kickoff)?.getTime() || 0) - (parseKickoff(b.kickoff)?.getTime() || 0));
  }, [selectedStage, hidePast, now]);

  const groupedMatches = useMemo(() => {
    const groups: Record<string, Match[]> = {};
    filteredMatches.forEach(m => {
      const dateStr = m.kickoff.split(' ')[0];
      if (!groups[dateStr]) groups[dateStr] = [];
      groups[dateStr].push(m);
    });
    return groups;
  }, [filteredMatches]);

  const getTeamName = (id: number | null, label: string, match?: Match, isHome?: boolean) => {
    if (id !== null && allTeams[id]) return allTeams[id].name;
    if (match && !id) {
        const pred = getMatchPrediction(match);
        const aiLabel = isHome ? pred?.predictedHomeTeamLabel : pred?.predictedAwayTeamLabel;
        if (aiLabel) return `(AI: ${aiLabel})`;
    }
    return label;
  };

  const getTeamFlag = (id: number | null) => {
    if (id !== null && allTeams[id]) return allTeams[id].flag;
    return '🏳️';
  };

  return (
    <div className="min-h-screen bg-slate-50 pb-20 selection:bg-blue-100 text-slate-900">
      <header className="bg-white/80 backdrop-blur-md border-b border-slate-200 sticky top-0 z-50">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex flex-col sm:flex-row justify-between items-center py-4 sm:h-24 gap-4">
            <div className="flex items-center gap-4 group cursor-pointer">
              <div className="bg-blue-600 p-3 rounded-[1.25rem] text-white shadow-xl shadow-blue-200 rotate-3 group-hover:rotate-0 transition-transform duration-500">
                <svg xmlns="http://www.w3.org/2000/svg" className="h-8 w-8" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3.055 11H5a2 2 0 012 2v1a2 2 0 002 2 2 2 0 012 2v2.945M8 3.935V5.5A2.5 2.5 0 0010.5 8h.5a2 2 0 012 2 2 2 0 104 0 2 2 0 012-2h1.064M15 20.488V18a2 2 0 012-2h3.064M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
              <div>
                <h1 className="text-3xl font-black tracking-tighter text-slate-900 leading-none">VM KULA 2026</h1>
                <p className="text-[10px] text-blue-600 font-black uppercase tracking-[0.3em] mt-1.5 flex items-center gap-2">
                    <span className="w-1.5 h-1.5 rounded-full bg-blue-600 animate-pulse"></span>
                    AI Predictions Enabled
                </p>
              </div>
            </div>
            
            <nav className="flex bg-slate-100 p-1.5 rounded-2xl border border-slate-200 shadow-inner">
              {(['tables', 'matches', 'venues'] as Tab[]).map(tab => (
                <button 
                  key={tab}
                  onClick={() => setActiveTab(tab)}
                  className={`px-6 py-2.5 rounded-xl text-xs font-black uppercase tracking-widest transition-all duration-300 ${activeTab === tab ? 'bg-white text-blue-600 shadow-md scale-105' : 'text-slate-500 hover:text-slate-900'}`}
                >
                  {tab === 'tables' ? 'Tabeller' : tab === 'matches' ? 'Kamper' : 'Stadioner'}
                </button>
              ))}
            </nav>
          </div>
        </div>
      </header>

      <main className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 mt-12">
        {activeTab === 'tables' && (
          <section className="animate-in fade-in slide-in-from-bottom-6 duration-700">
            <div className="mb-16 bg-gradient-to-br from-white to-slate-50 rounded-[3rem] p-10 border border-slate-200 shadow-2xl relative overflow-hidden group">
                <div className="absolute top-0 right-0 p-10 opacity-[0.03] rotate-12 group-hover:rotate-0 transition-transform duration-1000">
                    <svg width="240" height="240" viewBox="0 0 24 24" fill="currentColor">
                       <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 18c-4.41 0-8-3.59-8-8s3.59-8 8-8 8.3.59 8 8-3.59 8-8 8zm-5-9h10v2H7z"/>
                    </svg>
                </div>
                <div className="relative z-10">
                  <div className="flex items-center gap-3 mb-6">
                    <span className="bg-blue-600 text-white text-[9px] font-black px-3 py-1.5 rounded-lg uppercase tracking-[0.2em] shadow-lg shadow-blue-200">AI Deep Dive</span>
                  </div>
                  <h2 className="text-4xl font-black mb-6 tracking-tight text-slate-900 leading-tight">Veiene til New Jersey 2026</h2>
                  {loadingAnalysis ? (
                    <div className="space-y-4">
                      <div className="h-5 bg-slate-200/50 rounded-full w-full animate-pulse"></div>
                      <div className="h-5 bg-slate-200/50 rounded-full w-5/6 animate-pulse"></div>
                    </div>
                  ) : (
                    <div className="space-y-8">
                        <p className="text-slate-600 text-xl leading-relaxed font-medium">{analysis?.summary}</p>
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                            <div className="bg-white p-6 rounded-3xl border border-blue-100 shadow-sm">
                                <h4 className="text-[10px] font-black text-blue-600 uppercase mb-4 tracking-widest">Favoritter (AI Pick)</h4>
                                <div className="flex flex-wrap gap-2">
                                    {analysis?.favorites.map(f => <span key={f} className="px-4 py-2 bg-blue-50 text-blue-700 rounded-xl font-bold text-sm border border-blue-100">{f}</span>)}
                                </div>
                            </div>
                            <div className="bg-white p-6 rounded-3xl border border-amber-100 shadow-sm">
                                <h4 className="text-[10px] font-black text-amber-600 uppercase mb-4 tracking-widest">Spennende Outsidere</h4>
                                <div className="flex flex-wrap gap-2">
                                    {analysis?.darkHorses.map(d => <span key={d} className="px-4 py-2 bg-amber-50 text-amber-700 rounded-xl font-bold text-sm border border-amber-100">{d}</span>)}
                                </div>
                            </div>
                        </div>
                    </div>
                  )}
                </div>
            </div>

            <div className="flex flex-col gap-16">
              {INITIAL_GROUPS.map(group => {
                const groupPreds = analysis?.groupPredictions?.find(gp => gp.groupId === group.id)?.predictions;
                return (
                    <GroupCard 
                        key={group.id} 
                        group={group} 
                        predictions={groupPreds}
                    />
                );
              })}
            </div>
          </section>
        )}

        {activeTab === 'matches' && (
          <section className="animate-in fade-in slide-in-from-bottom-6 duration-700">
             <div className="bg-white p-10 rounded-[3rem] border border-slate-200 mb-12 shadow-xl shadow-slate-200/50">
                <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-8 mb-10">
                   <div>
                      <h2 className="text-3xl font-black text-slate-900 tracking-tight">Kampskjema</h2>
                      <p className="text-sm text-slate-400 font-bold uppercase tracking-widest mt-1">Med intelligente AI-prediksjoner</p>
                   </div>
                   <div className="flex items-center gap-6 bg-slate-50 p-3 rounded-2xl border border-slate-100">
                      <div className="flex flex-col items-end">
                        <span className="text-[10px] font-black text-slate-500 uppercase tracking-widest">Fokuser på fremtiden</span>
                        <span className="text-[9px] text-slate-400 font-bold">Skjul ferdige kamper</span>
                      </div>
                      <button 
                         onClick={() => setHidePast(!hidePast)}
                         className={`relative inline-flex h-7 w-14 items-center rounded-full transition-all duration-500 ${hidePast ? 'bg-blue-600 shadow-lg shadow-blue-200' : 'bg-slate-300'}`}
                      >
                         <span className={`inline-block h-5 w-5 transform rounded-full bg-white transition-transform duration-500 ${hidePast ? 'translate-x-8' : 'translate-x-1'}`} />
                      </button>
                   </div>
                </div>

                <div className="overflow-x-auto pb-4 -mx-2 flex gap-3 px-2">
                   <button onClick={() => setSelectedStage('all')} className={`px-6 py-3 rounded-2xl text-[10px] font-black uppercase tracking-widest border transition-all duration-300 whitespace-nowrap ${selectedStage === 'all' ? 'bg-blue-600 text-white border-blue-600 shadow-lg shadow-blue-100' : 'bg-white text-slate-500 border-slate-200 hover:border-blue-200'}`}>Alle runder</button>
                   {STAGES.map(stage => (
                      <button key={stage.id} onClick={() => setSelectedStage(stage.id)} className={`px-6 py-3 rounded-2xl text-[10px] font-black uppercase tracking-widest border transition-all duration-300 whitespace-nowrap ${selectedStage === stage.id ? 'bg-blue-600 text-white border-blue-600 shadow-lg shadow-blue-100' : 'bg-white text-slate-500 border-slate-200 hover:border-blue-200'}`}>{stage.name}</button>
                   ))}
                </div>
             </div>

             <div className="space-y-20">
                {Object.keys(groupedMatches).length === 0 ? (
                  <div className="bg-white rounded-[3rem] p-24 text-center border border-dashed border-slate-300 text-slate-400 font-black italic uppercase tracking-widest">
                    Ingen kamper funnet i valgt runder.
                  </div>
                ) : (
                  Object.entries(groupedMatches).map(([date, matches]) => (
                    <div key={date} className="relative">
                      <div className="sticky top-28 z-30 mb-10 flex justify-center">
                        <div className="bg-slate-900 text-white px-8 py-3 rounded-full shadow-2xl border border-white/20 backdrop-blur-md">
                          <span className="text-sm font-black uppercase tracking-[0.2em]">{new Date(date).toLocaleDateString('no-NO', { weekday: 'long', day: 'numeric', month: 'long', year: 'numeric' })}</span>
                        </div>
                      </div>
                      <div className="grid gap-8">
                        {matches.map(match => {
                          const venue = VENUES.find(v => v.id === match.cityId);
                          const kd = parseKickoff(match.kickoff);
                          const isPast = kd && kd.getTime() + (2 * 60 * 60 * 1000) < now.getTime();
                          const pred = getMatchPrediction(match);
                          const isKnockout = match.stageId > 1;
                          
                          return (
                            <div key={match.id} className={`bg-white rounded-[2.5rem] p-10 border-2 transition-all duration-500 group ${isPast ? 'opacity-40 grayscale scale-[0.98]' : 'border-slate-100 shadow-xl hover:shadow-2xl hover:border-blue-300 hover:-translate-y-1'}`}>
                               <div className="flex justify-between items-center mb-10">
                                  <div className="flex items-center gap-3">
                                    <span className="text-[10px] font-black uppercase tracking-[0.2em] text-blue-600 bg-blue-50 px-4 py-2 rounded-xl border border-blue-100">Kamp {match.matchNumber}</span>
                                    {isKnockout && (
                                        <span className="text-[9px] font-black uppercase tracking-widest text-amber-600 bg-amber-50 px-3 py-1.5 rounded-lg border border-amber-100">Sluttspill Simulering</span>
                                    )}
                                  </div>
                                  <div className="flex items-center gap-3 text-[11px] font-black text-slate-500 uppercase tracking-widest">
                                    <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4 text-blue-500" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
                                    {kd?.toLocaleTimeString('no-NO', { hour: '2-digit', minute: '2-digit' })} Lokal tid
                                  </div>
                               </div>
                               
                               <div className="grid grid-cols-7 items-center gap-6 mb-12">
                                  <div className="col-span-3 flex flex-col items-center gap-4">
                                     <span className="text-7xl drop-shadow-lg group-hover:scale-110 transition-transform duration-500">{getTeamFlag(match.homeTeamId)}</span>
                                     <span className="text-xl font-black text-slate-900 text-center leading-tight tracking-tight uppercase">
                                        {getTeamName(match.homeTeamId, match.label.split(' vs ')[0], match, true)}
                                     </span>
                                  </div>
                                  <div className="col-span-1 flex flex-col items-center">
                                     <div className="w-16 h-16 rounded-full bg-slate-50 flex items-center justify-center border-2 border-slate-100">
                                        <span className="font-black text-2xl text-slate-300 italic">VS</span>
                                     </div>
                                  </div>
                                  <div className="col-span-3 flex flex-col items-center gap-4">
                                     <span className="text-7xl drop-shadow-lg group-hover:scale-110 transition-transform duration-500">{getTeamFlag(match.awayTeamId)}</span>
                                     <span className="text-xl font-black text-slate-900 text-center leading-tight tracking-tight uppercase">
                                        {getTeamName(match.awayTeamId, match.label.split(' vs ')[1], match, false)}
                                     </span>
                                  </div>
                               </div>

                               {!isPast && pred && (
                                   <div className="bg-blue-50/50 rounded-3xl p-6 border border-blue-100 flex flex-col sm:flex-row items-center gap-6">
                                       <div className="flex-shrink-0 bg-white p-4 rounded-2xl shadow-sm border border-blue-100 text-center">
                                            <span className="text-[9px] font-black text-blue-400 uppercase block mb-1">AI Prob</span>
                                            <span className="text-3xl font-black text-blue-600">{pred.winProbability}%</span>
                                       </div>
                                       <div className="flex-1">
                                            <p className="text-sm font-bold text-blue-900 leading-relaxed">
                                                <span className="text-blue-500 font-black uppercase text-[10px] tracking-widest mr-2">AI Analyse:</span>
                                                {pred.reasoning}
                                            </p>
                                            <div className="flex items-center gap-3 mt-3">
                                                <div className="bg-white px-4 py-1.5 rounded-xl border border-blue-100 text-[11px] font-black text-blue-600 uppercase tracking-widest">
                                                    Forventet: {pred.predictedHomeScore} - {pred.predictedAwayScore}
                                                </div>
                                                {pred.predictedWinnerLabel && (
                                                    <div className="bg-green-50 px-4 py-1.5 rounded-xl border border-green-100 text-[11px] font-black text-green-600 uppercase tracking-widest">
                                                        Vinner: {pred.predictedWinnerLabel}
                                                    </div>
                                                )}
                                            </div>
                                       </div>
                                   </div>
                               )}

                               <div className="mt-10 pt-8 border-t border-slate-100 flex flex-col sm:flex-row items-center justify-between gap-6">
                                  <div className="flex items-center gap-3">
                                    <div className="w-10 h-10 rounded-xl bg-slate-100 flex items-center justify-center text-blue-600 shadow-inner">
                                        <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" /><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" /></svg>
                                    </div>
                                    <div className="flex flex-col">
                                        <span className="text-sm font-black tracking-tight text-slate-900 uppercase">{venue?.stadium}</span>
                                        <span className="text-[10px] font-bold text-slate-400 uppercase tracking-widest">{venue?.city}, {venue?.country}</span>
                                    </div>
                                  </div>
                               </div>
                            </div>
                          );
                        })}
                      </div>
                    </div>
                  ))
                )}
             </div>
          </section>
        )}

        {activeTab === 'venues' && (
          <section className="animate-in fade-in slide-in-from-bottom-6 duration-700">
             <div className="grid grid-cols-1 md:grid-cols-2 gap-10">
                {VENUES.map(venue => (
                  <div key={venue.id} className="bg-white rounded-[3rem] p-10 border border-slate-200 shadow-xl group hover:border-blue-300 transition-all hover:-translate-y-2">
                     <div className="flex justify-between items-start mb-8">
                        <div className="flex flex-col gap-1">
                            <h3 className="text-3xl font-black text-slate-900 tracking-tight">{venue.city}</h3>
                            <span className="text-xs font-bold text-slate-400 uppercase tracking-widest">{venue.country}</span>
                        </div>
                        <div className="w-12 h-12 rounded-2xl bg-blue-50 flex items-center justify-center text-blue-600 group-hover:bg-blue-600 group-hover:text-white transition-colors duration-500">
                           <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor"><path d="M7 11V7l5-5 5 5v4h3l1 1v7l-1 1H5l-1-1v-7l1-1h2z"/></svg>
                        </div>
                     </div>
                     <p className="text-slate-600 font-bold text-lg mb-10 leading-snug">{venue.stadium}</p>
                     <div className="flex items-center justify-between pt-8 border-t border-slate-100">
                        <div className="flex flex-col">
                          <span className="text-[10px] font-black text-slate-400 uppercase tracking-widest mb-1">Region</span>
                          <span className="text-sm font-black text-slate-800">{venue.region}</span>
                        </div>
                        <div className="flex flex-col items-end">
                          <span className="text-[10px] font-black text-slate-400 uppercase tracking-widest mb-1">Intl Airport</span>
                          <span className="text-sm font-black text-slate-800">{venue.airport}</span>
                        </div>
                     </div>
                  </div>
                ))}
             </div>
          </section>
        )}
      </main>

      <footer className="mt-40 border-t border-slate-200 bg-white py-32 text-center">
        <div className="max-w-md mx-auto px-4">
            <p className="text-slate-900 font-black text-4xl tracking-tighter mb-4">VM KULA 2026</p>
            <p className="text-slate-400 text-sm font-medium leading-relaxed mb-12">Det ultimate verktøyet for deg som vil ha overtaket før mesterskapet blåses i gang. Ved hjelp av Gemini AI-modeller forutsier vi spenningen.</p>
            <div className="flex justify-center gap-3">
                <div className="w-2 h-2 rounded-full bg-slate-200"></div>
                <div className="w-8 h-2 rounded-full bg-blue-600"></div>
                <div className="w-2 h-2 rounded-full bg-slate-200"></div>
            </div>
            <p className="text-[10px] text-slate-300 font-black uppercase tracking-[0.3em] mt-12">© 2026 World Cup Unofficial Companion App</p>
        </div>
      </footer>
    </div>
  );
};

export default App;
