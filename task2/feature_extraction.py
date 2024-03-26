import javalang

for token in javalang.tokenizer.tokenize("""public static void main(String[] args) {
    System.out.println("Hello world!");
}
"""):
    print(token)