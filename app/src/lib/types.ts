export interface Message {
    paint_image: string;
    text_voice: string;
    intro_voice: string;
    scene_image_description: string;
    message_index: number;
    image: string;
    audio: string;
}

export interface SubmitImageResponse {
    is_correct: boolean;
    feedback: string;
}

export interface SubmitImageMessage {
    message_index: number;
    audio: string;
    image: string | null;
    data: SubmitImageResponse;
}

export interface Story {
    chat_id: string;
    title: string;
    chat_image: string;
    last_update: string;
    messages: Message[];
    subimits: SubmitImageMessage[];
    voice_name: string;
}

export interface ChatsAndVoices {
    chats: Story[];
    available_voices: string[];
}
