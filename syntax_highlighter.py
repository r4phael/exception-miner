import highlighter
import jsbeautifier
import javalang


def print_highlight(code: str, line_highlights=[]) -> None:
    html, css = highlighter.highlight(
        ["pre", {}, code], lang="Java", output="html", lineHighlights=line_highlights)
    display(HTML(
        f"{html}<style>pre {{background-color: #fff; font-weight: bold}}</style><style>{css}</style>"))


def format_and_print_highlight(front, back, mask, esperado=None, gerado=None):
    assert isinstance(mask, list), print(type(mask))
    code = front + back
    if (esperado):
        code += "\n// Codigo Esperado \n" + esperado
    if (gerado):
        code += "\n// Codigo Gerado \n" + gerado
    code += "}"


    beautify_print(code, mask)

def format_and_print_highlight_v2(front, back, mask, esperado=None, gerado=None):
    assert isinstance(mask, list), print(type(mask))

    code = front + back + "}" + esperado
    repeat = code.count("{") 
    repeat -= code.count("}")
    code += ("}" * repeat) + "\n"
    
    code_gerado = front + back + "}" + gerado
    repeat = code_gerado.count("{") 
    repeat -= code_gerado.count("}")
    code_gerado += ("}" * repeat) + "\n"

    beautify_print(code + code_gerado, mask)

def beautify_print(code, mask):
    code = jsbeautifier.beautify(code)

    highlight_lines = set()
    mask_pos = 0
    for line_number, line in enumerate(code.split('\n')):
        tokens = list(javalang.tokenizer.tokenize(line))
        if (mask_pos >= len(mask)):
            break
        offset_string = 0
        for i, token in enumerate(tokens):
            if (type(token) == javalang.tokenizer.String):
                offset_string += len(token.value.split(' ')) - 1
            elif (mask[mask_pos + offset_string + i] == 1):
                highlight_lines.add(line_number + 1)
        mask_pos += len(tokens) + offset_string

    print_highlight(code, highlight_lines)


if __name__ == '__main__':
    # Testes

    # format_and_print_highlight('public static void main ( String [ ] args ) { int a = 10 ; for ( int i = 3 ; i >= 0 ; i -- )',
    #                            'try { System . out . println ( a / i ) ;',
    #                            [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 1, 1, 1, 1,
    #                             0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]).split('\n')
    print_highlight("""public class Main {
        public static void main(String[] args) {
            System.out.println("Hello World!");
        }
    }""", set([2, 3]))
    print()
    format_and_print_highlight('public String currentLabel ( ) {',
                               'try { File file = ( File ) f . get ( reader ) ; return file . getParentFile ( ) . getName ( ) ;',
                               [0 + 1])
        
