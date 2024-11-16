from transformers import GPT2LMHeadModel, GPT2Tokenizer

# Load pre-trained GPT-2 model and tokenizer
model_name = 'gpt2'  # You can also use 'gpt2-medium', 'gpt2-large', or 'gpt2-xl'
model = GPT2LMHeadModel.from_pretrained(model_name)
tokenizer = GPT2Tokenizer.from_pretrained(model_name)

# Set the model to evaluation mode
model.eval()
def generate_long_paragraph(prompt_given, max_length=450):  # Increase max_length to make the output bigger
    # Encode the prompt text
    inputs = tokenizer.encode(prompt_given, return_tensors='pt')

    # Generate text
    output = model.generate(
        inputs,
        max_length=max_length,  # Increased length for a larger paragraph
        num_return_sequences=1,  # Generate one sequence
        no_repeat_ngram_size=2,  # Avoid repeating n-grams
        top_p=0.9,  # Nucleus sampling
        top_k=50,  # Top-K sampling to control diversity
        temperature=0.7,  # Lower temperature for more controlled output
        pad_token_id=tokenizer.eos_token_id  # Handle padding correctly
    )

    # Decode the generated text and return it
    generated_text = tokenizer.decode(output[0], skip_special_tokens=True)
    return generated_text
