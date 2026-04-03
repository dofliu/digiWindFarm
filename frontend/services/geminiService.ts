
import { GoogleGenAI } from "@google/genai";
import { type TurbineData } from '../types';

export const analyzeTurbineFault = async (turbineData: TurbineData): Promise<string> => {
  if (!process.env.API_KEY) {
    return Promise.resolve("API Key not configured. Please set the API_KEY environment variable. This is a sample response.\n\n**Potential Cause:** High Vibration Sensor Anomaly\n\n**Recommended Actions:**\n1. Verify vibration readings with a portable sensor.\n2. Inspect the main bearing for physical damage.\n3. Check lubrication system pressure and levels.");
  }

  try {
    const ai = new GoogleGenAI({ apiKey: process.env.API_KEY });
    const model = 'gemini-2.5-flash';

    const dataSnapshot = { ...turbineData };
    // @ts-ignore
    delete dataSnapshot.history; // Don't send the long history array to the model

    const prompt = `
      You are an expert wind turbine maintenance AI.
      A wind turbine has entered a FAULT state. Analyze the following data snapshot and provide a concise diagnosis.
      
      Your response should include:
      1. A "Likely Cause" for the fault.
      2. A numbered list of "Recommended Actions" for a technician to take.
      
      Keep the language professional and direct.

      Turbine Data:
      ${JSON.stringify(dataSnapshot, null, 2)}
    `;

    const response = await ai.models.generateContent({
      model,
      contents: prompt,
    });
    
    return response.text;

  } catch (error) {
    console.error("Error calling Gemini API:", error);
    if (error instanceof Error) {
        return `An error occurred while analyzing the fault: ${error.message}`;
    }
    return "An unknown error occurred while analyzing the fault.";
  }
};
