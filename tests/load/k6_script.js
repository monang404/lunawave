import ws from 'k6/ws';
import { check } from 'k6';
import { sleep } from 'k6';

export const options = {
    vus: 50,
    duration: '10s',
};

export default function () {
    const url = 'ws://localhost:8765/ws';
    const res = ws.connect(url, {}, function (socket) {
        socket.on('open', function () {
            socket.send(JSON.stringify({ type: 'get_state', data: null }));
        });

        socket.on('message', function (msg) {
            const parsed = JSON.parse(msg);
            check(parsed, {
                'received state or log': (p) => p.type === 'state' || p.type === 'log',
            });
            socket.close();
        });
        
        socket.setTimeout(function () {
            socket.close();
        }, 3000);
    });
    
    check(res, { 'status is 101': (r) => r && r.status === 101 });
}
