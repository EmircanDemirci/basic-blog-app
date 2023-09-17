const express = require("express");
const morgan = require("morgan");
const mongoose = require("mongoose");
const Blog = require("./models/blog");
const blogRouters = require("./router/blogRouter")


//express app
const app = express();



//connect to mongodb
const dbURI = "mongodb+srv://venoox:test1234@cluster0.a9ct3mq.mongodb.net/?retryWrites=true&w=majority";
mongoose.connect(dbURI , {useNewUrlParser:true,useUnifiedTopology:true})
.then(result=>{
    console.log("connected");
    app.listen(4000);
})
.catch((err)=> console.log(err));


//view engine
app.set('view engine' , 'ejs');
app.engine('ejs', require('ejs').__express);

//middleware and static files
app.use(express.static('public'));
app.use(express.urlencoded({extended:true}));
app.use(morgan('dev'));


//mongoose and mongo sandbox routers
app.use("/blog" , blogRouters);


//routers
app.get("/" , (req,res)=>{
    res.redirect("/blog")
})

app.get("/about" , (req,res)=>{
    res.render('about.ejs');
})

app.get("/create" ,(req,res)=>{
    res.render('create.ejs');
})

//redirect
app.get("/about-me" , (req,res)=>{
    res.redirect("/about");
})

//404

app.use((req,res)=>{
    res.status(404).render("404.ejs")
})

