'use server';

/**
 * @fileOverview Generates a drawing based on a recorded story and existing drawing.
 *
 * - generateDrawingFromStory - A function that generates a drawing from a story and existing drawing.
 * - GenerateDrawingFromStoryInput - The input type for the generateDrawingFromStory function.
 * - GenerateDrawingFromStoryOutput - The return type for the generateDrawingFromStory function.
 */

import {ai} from '@/ai/genkit';
import {z} from 'genkit';

const GenerateDrawingFromStoryInputSchema = z.object({
  storyAudioDataUri: z
    .string()
    .describe(
      'The recorded story as a data URI that must include a MIME type and use Base64 encoding. Expected format: \'data:<mimetype>;base64,<encoded_data>\'.'
    ),
  existingDrawingDataUri: z
    .string()
    .describe(
      'The existing drawing as a data URI that must include a MIME type and use Base64 encoding. Expected format: \'data:<mimetype>;base64,<encoded_data>\'.'
    )
    .optional(),
});
export type GenerateDrawingFromStoryInput = z.infer<
  typeof GenerateDrawingFromStoryInputSchema
>;

const GenerateDrawingFromStoryOutputSchema = z.object({
  generatedDrawingDataUri: z.string().describe('The generated drawing as a data URI.'),
});
export type GenerateDrawingFromStoryOutput = z.infer<
  typeof GenerateDrawingFromStoryOutputSchema
>;

export async function generateDrawingFromStory(
  input: GenerateDrawingFromStoryInput
): Promise<GenerateDrawingFromStoryOutput> {
  return generateDrawingFromStoryFlow(input);
}

const prompt = ai.definePrompt({
  name: 'generateDrawingFromStoryPrompt',
  input: {schema: GenerateDrawingFromStoryInputSchema},
  output: {schema: GenerateDrawingFromStoryOutputSchema},
  prompt: `You are a children's book illustrator. You will generate a drawing based on a recorded story and an existing drawing, if one exists.

  Story: {{media url=storyAudioDataUri}}
  {{#if existingDrawingDataUri}}
  Existing Drawing: {{media url=existingDrawingDataUri}}
  {{/if}}

  Generate a new drawing that visually represents the story and incorporates elements from the existing drawing.
  Return the drawing as a data URI in the 'generatedDrawingDataUri' field.
  `,
});

const generateDrawingFromStoryFlow = ai.defineFlow(
  {
    name: 'generateDrawingFromStoryFlow',
    inputSchema: GenerateDrawingFromStoryInputSchema,
    outputSchema: GenerateDrawingFromStoryOutputSchema,
  },
  async input => {
    const {media} = await ai.generate({
      model: 'googleai/gemini-2.0-flash-preview-image-generation',
      prompt: [
        {
          media: {url: input.storyAudioDataUri},
        },
        {
          text: `Generate a drawing that visually represents the story. ${input.existingDrawingDataUri ? 'Incorporate elements from the existing drawing: ' + input.existingDrawingDataUri : ''}`,
        },
      ],
      config: {
        responseModalities: ['TEXT', 'IMAGE'],
      },
    });

    return {
      generatedDrawingDataUri: media!.url,
    };
  }
);
