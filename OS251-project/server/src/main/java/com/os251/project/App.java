package com.os251.project;

import io.javalin.Javalin;
import io.javalin.staticfiles.Location;
import io.javalin.websocket.WsSession;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;

public class App {

    private static Map<String, Collab> collabs = new ConcurrentHashMap<>();

    private static Collab getCollab(WsSession session) {
        return collabs.get(session.pathParam("doc-id"));
    }

    private static void createCollab(WsSession session) {
        collabs.put(session.pathParam("doc-id"), new Collab());
    }

    public static void main(String[] args){
        System.out.println(System.getProperty("user.dir"));
        Javalin.create()
                .enableStaticFiles("/public")
                .ws("/docs/:doc-id", ws -> {
                    ws.onConnect(session -> {
                        if (getCollab(session) == null) {
                            createCollab(session);
                        }
                        getCollab(session).sessions.add(session);
                        session.send(getCollab(session).doc);
                    });
                    ws.onMessage((session, message) -> {
                        getCollab(session).doc = message;
                        getCollab(session).sessions.stream().filter(WsSession::isOpen).forEach(s -> {
                            s.send(getCollab(session).doc);
                        });
                    });
                    ws.onClose((session, status, message) -> {
                        getCollab(session).sessions.remove(session);
                    });
                })
                .start(7070);
    }
}
