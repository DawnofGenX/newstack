// Reads HOST/PORT and serves until killed.

package textstat

class App {
    static void main(String[] args) {
        String host = System.getenv('HOST') ?: '127.0.0.1'
        String portText = System.getenv('PORT') ?: '8080'
        Server.serve(host, Integer.parseInt(portText))
    }
}
