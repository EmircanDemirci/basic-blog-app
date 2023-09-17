const express = require("express");
const Blog = require("./../models/blog");

const router = express.Router();

//blog routers

router.get("/" , (req,res)=>{
    Blog.find().sort({createAt:-1})
    .then(result=>res.render("index.ejs",{title:"Home" , blogs:result}))
    .catch(err=>console.log(err))
})

router.get("/:id" , (req,res)=>{
    const id = req.params.id;
    Blog.findById(id)
    .then(result=>{
        res.render("detail" , {blog:result , title:"Blog Details"})
    })
    .catch(err=>console.log(err))
})

router.post("/" , (req,res)=>{
    const blog = new Blog(req.body);
    blog.save()
    .then(result=> res.redirect("/blog"));
})

router.delete("/:id" , (req,res)=>{
    const id = req.params.id;
    Blog.findByIdAndDelete(id)
    .then(result=> res.json({redirect:"/blog"}))
    .catch(err=>console.log(err));
})

module.exports = router