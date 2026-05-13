import { initializeApp } from "firebase/app";
import { getFirestore } from "firebase/firestore";

const firebaseConfig = {
  apiKey: "AIzaSyAcFUdU5pj0KutB_j1patphb95Y7p7TfQE",
  authDomain: "kosmes-605c2.firebaseapp.com",
  projectId: "kosmes-605c2",
  storageBucket: "kosmes-605c2.firebasestorage.app",
  messagingSenderId: "62008966815",
  appId: "1:62008966815:web:9b2aae03d07e665dbc2caa",
};

const app = initializeApp(firebaseConfig);
export const db = getFirestore(app, "kosmes");
