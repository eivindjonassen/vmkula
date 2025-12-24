
import { GoogleGenAI, Type } from "@google/genai";
import { AIAnalysis } from "../types";

const ai = new GoogleGenAI({ apiKey: process.env.API_KEY });

export async function getWorldCupAnalysis(): Promise<AIAnalysis> {
  const fullTeamMap = `
    ID-LISTE FOR ALLE LAG (VIKTIG: BRUK KUN DISSE ID-ENE):
    A: 1:Mexico, 2:Sør-Afrika, 3:Sør-Korea, 4:UEFA-D
    B: 5:Canada, 6:UEFA-A, 7:Qatar, 8:Sveits
    C: 9:Brasil, 10:Marokko, 11:Haiti, 12:Skottland
    D: 13:USA, 14:Paraguay, 15:Australia, 16:UEFA-C
    E: 17:Tyskland, 18:Curaçao, 19:Elfenbenskysten, 20:Ecuador
    F: 21:Nederland, 22:Japan, 23:UEFA-B, 24:Tunisia
    G: 25:Belgia, 26:Egypt, 27:Iran, 28:New Zealand
    H: 29:Spania, 30:Kapp Verde, 31:Saudi-Arabia, 32:Uruguay
    I: 33:Frankrike, 34:Senegal, 35:FIFA-Playoff-2, 36:Norge
    J: 37:Argentina, 38:Algerie, 39:Østerrike, 40:Jordan
    K: 41:Portugal, 42:FIFA-Playoff-1, 43:Usbekistan, 44:Colombia
    L: 45:England, 46:Kroatia, 47:Ghana, 48:Panama
  `;

  const response = await ai.models.generateContent({
    model: "gemini-3-flash-preview",
    contents: `Du er en verdensledende fotballanalytiker. Analyser FIFA VM 2026.
    
    ${fullTeamMap}
    
    OPPGAVE:
    1. Gi en prediksjon for sluttplassering (rank 1-4) for SAMTLIGE 48 lag i deres respektive grupper.
    2. Skriv en kort analyse for HVERT lag.
    3. Prediker turneringsbanen for utslagskamper (kamp 73-104). 
       FOR HVER KAMP (73-104): Spesifiser hvem du tror spiller (f.eks. "Frankrike"), forventet skåring (f.eks. 2-1), og vinneren.
    
    Svar på norsk i JSON-format.`,
    config: {
      responseMimeType: "application/json",
      responseSchema: {
        type: Type.OBJECT,
        properties: {
          summary: { type: Type.STRING },
          favorites: { type: Type.ARRAY, items: { type: Type.STRING } },
          darkHorses: { type: Type.ARRAY, items: { type: Type.STRING } },
          groupPredictions: {
            type: Type.ARRAY,
            items: {
              type: Type.OBJECT,
              properties: {
                groupId: { type: Type.STRING },
                predictions: {
                  type: Type.ARRAY,
                  items: {
                    type: Type.OBJECT,
                    properties: {
                      teamId: { type: Type.INTEGER },
                      rank: { type: Type.INTEGER },
                      note: { type: Type.STRING }
                    },
                    required: ["teamId", "rank", "note"]
                  }
                }
              },
              required: ["groupId", "predictions"]
            }
          },
          tournamentPath: {
            type: Type.ARRAY,
            items: {
              type: Type.OBJECT,
              properties: {
                matchNumber: { type: Type.INTEGER },
                homeLabel: { type: Type.STRING },
                awayLabel: { type: Type.STRING },
                predictedHomeScore: { type: Type.INTEGER },
                predictedAwayScore: { type: Type.INTEGER },
                winnerLabel: { type: Type.STRING }
              },
              required: ["matchNumber", "homeLabel", "awayLabel", "predictedHomeScore", "predictedAwayScore", "winnerLabel"]
            }
          }
        },
        required: ["summary", "favorites", "darkHorses", "groupPredictions", "tournamentPath"]
      }
    }
  });

  try {
    return JSON.parse(response.text.trim());
  } catch (error) {
    console.error("Failed to parse AI response", error);
    throw error;
  }
}
